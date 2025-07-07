# Phase 2 Implementation Guide: Angular Frontend Development

## Overview

Phase 2 transforms GenStoryAI from an API-only system into a full-featured web application using Angular 18. This guide provides step-by-step instructions for building a modern, responsive frontend that leverages the latest Angular features including standalone components, signals, and the new control flow syntax.

## Timeline: 4 Weeks

- **Week 1**: Angular project setup, core module, authentication
- **Week 2**: Character management module  
- **Week 3**: Story creation wizard
- **Week 4**: Basic story reader implementation

## Prerequisites

- Node.js 18+ and npm 9+
- Angular CLI 18
- Basic knowledge of TypeScript and RxJS
- Backend API from Phase 1 running locally

## Week 1: Project Foundation & Authentication

### Step 1: Initialize Angular Project

#### 1.1 Create New Angular Project
```bash
# Install latest Angular CLI globally
npm install -g @angular/cli@18

# Create new project with routing and SCSS
ng new genstory-frontend --routing --style=scss --strict

# Navigate to project
cd genstory-frontend

# Add Angular Material
ng add @angular/material

# Install additional dependencies
npm install @angular/cdk @ngrx/store @ngrx/effects @ngrx/entity
npm install tailwindcss @tailwindcss/forms @tailwindcss/typography
npm install axios jwt-decode date-fns
```

#### 1.2 Configure Tailwind CSS
```bash
# Initialize Tailwind
npx tailwindcss init
```

Update `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e3f2fd',
          100: '#bbdefb',
          200: '#90caf9',
          300: '#64b5f6',
          400: '#42a5f5',
          500: '#2196f3',
          600: '#1e88e5',
          700: '#1976d2',
          800: '#1565c0',
          900: '#0d47a1',
        },
      },
      fontFamily: {
        'story': ['Georgia', 'serif'],
        'display': ['Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

Update `src/styles.scss`:
```scss
@use '@angular/material' as mat;
@tailwind base;
@tailwind components;
@tailwind utilities;

// Custom Material theme
@include mat.core();

$primary: mat.define-palette(mat.$indigo-palette);
$accent: mat.define-palette(mat.$pink-palette, A200, A100, A400);
$warn: mat.define-palette(mat.$red-palette);

$theme: mat.define-light-theme((
  color: (
    primary: $primary,
    accent: $accent,
    warn: $warn,
  ),
  typography: mat.define-typography-config(),
  density: 0,
));

@include mat.all-component-themes($theme);

// Global styles
html, body { 
  height: 100%; 
  margin: 0;
  font-family: Roboto, "Helvetica Neue", sans-serif;
}

// Custom utility classes
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 
           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
           transition-colors duration-200;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6 border border-gray-100;
  }
  
  .input-field {
    @apply block w-full rounded-md border-gray-300 shadow-sm 
           focus:border-primary-500 focus:ring-primary-500;
  }
}
```

#### 1.3 Configure Environment Files
```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  appName: 'GenStoryAI',
  tokenKey: 'genstory_token',
  refreshTokenKey: 'genstory_refresh_token',
};

// src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://api.genstory.ai',
  appName: 'GenStoryAI',
  tokenKey: 'genstory_token',
  refreshTokenKey: 'genstory_refresh_token',
};
```

### Step 2: Create Core Module

#### 2.1 Generate Core Module Structure
```bash
# Generate core module
ng generate module core

# Generate services
ng generate service core/services/auth --skip-tests
ng generate service core/services/api --skip-tests
ng generate service core/services/storage --skip-tests
ng generate service core/services/notification --skip-tests

# Generate guards
ng generate guard core/guards/auth --skip-tests
ng generate guard core/guards/role --skip-tests

# Generate interceptors
ng generate interceptor core/interceptors/auth --skip-tests
ng generate interceptor core/interceptors/error --skip-tests
```

#### 2.2 Implement API Service
```typescript
// src/app/core/services/api.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  get<T>(path: string, params?: HttpParams): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${path}`, { params })
      .pipe(catchError(this.handleError));
  }

  post<T>(path: string, body: any = {}): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${path}`, body)
      .pipe(catchError(this.handleError));
  }

  put<T>(path: string, body: any = {}): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}${path}`, body)
      .pipe(catchError(this.handleError));
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}${path}`)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: any): Observable<never> {
    console.error('API Error:', error);
    return throwError(() => error);
  }
}
```

#### 2.3 Implement Auth Service
```typescript
// src/app/core/services/auth.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, BehaviorSubject, tap, map, catchError, of } from 'rxjs';
import { ApiService } from './api.service';
import { StorageService } from './storage.service';
import { environment } from '../../../environments/environment';

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private api = inject(ApiService);
  private storage = inject(StorageService);
  private router = inject(Router);
  
  // Using signals for reactive state
  private currentUserSignal = signal<User | null>(null);
  private isLoadingSignal = signal(false);
  
  // Computed values
  currentUser = this.currentUserSignal.asReadonly();
  isAuthenticated = computed(() => !!this.currentUserSignal());
  isLoading = this.isLoadingSignal.asReadonly();

  constructor() {
    this.checkStoredAuth();
  }

  private checkStoredAuth(): void {
    const token = this.storage.get(environment.tokenKey);
    if (token) {
      this.loadCurrentUser().subscribe();
    }
  }

  login(credentials: LoginCredentials): Observable<User> {
    this.isLoadingSignal.set(true);
    
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    return this.api.post<AuthResponse>('/auth/jwt/login', formData).pipe(
      tap(response => this.storeTokens(response)),
      tap(() => this.router.navigate(['/dashboard'])),
      tap(() => this.loadCurrentUser().subscribe()),
      map(() => this.currentUserSignal()!),
      tap(() => this.isLoadingSignal.set(false)),
      catchError(error => {
        this.isLoadingSignal.set(false);
        throw error;
      })
    );
  }

  register(data: RegisterData): Observable<User> {
    this.isLoadingSignal.set(true);
    
    return this.api.post<User>('/auth/register', data).pipe(
      tap(() => this.isLoadingSignal.set(false)),
      catchError(error => {
        this.isLoadingSignal.set(false);
        throw error;
      })
    );
  }

  logout(): void {
    this.storage.remove(environment.tokenKey);
    this.storage.remove(environment.refreshTokenKey);
    this.currentUserSignal.set(null);
    this.router.navigate(['/auth/login']);
  }

  loadCurrentUser(): Observable<User | null> {
    return this.api.get<User>('/users/me').pipe(
      tap(user => this.currentUserSignal.set(user)),
      catchError(() => {
        this.logout();
        return of(null);
      })
    );
  }

  private storeTokens(response: AuthResponse): void {
    this.storage.set(environment.tokenKey, response.access_token);
  }

  getToken(): string | null {
    return this.storage.get(environment.tokenKey);
  }

  requestPasswordReset(email: string): Observable<any> {
    return this.api.post('/auth/forgot-password', { email });
  }

  resetPassword(token: string, password: string): Observable<any> {
    return this.api.post('/auth/reset-password', { token, password });
  }
}
```

#### 2.4 Implement Auth Interceptor
```typescript
// src/app/core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { environment } from '../../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();
  
  // Skip auth header for auth endpoints
  if (req.url.includes('/auth/') && !req.url.includes('/auth/me')) {
    return next(req);
  }
  
  if (token) {
    const authReq = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`)
    });
    return next(authReq);
  }
  
  return next(req);
};
```

#### 2.5 Implement Auth Guard
```typescript
// src/app/core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { map, take } from 'rxjs/operators';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  // Using signals, we can directly check the computed value
  if (authService.isAuthenticated()) {
    return true;
  }
  
  // Store attempted URL for redirecting after login
  const returnUrl = state.url;
  router.navigate(['/auth/login'], { queryParams: { returnUrl } });
  return false;
};
```

### Step 3: Create Authentication Module

#### 3.1 Generate Auth Components
```bash
# Generate auth module
ng generate module features/auth --routing

# Generate components
ng generate component features/auth/pages/login --standalone
ng generate component features/auth/pages/register --standalone
ng generate component features/auth/pages/forgot-password --standalone
ng generate component features/auth/pages/reset-password --standalone
ng generate component features/auth/components/auth-layout --standalone
```

#### 3.2 Implement Login Component
```typescript
// src/app/features/auth/pages/login/login.component.ts
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4">
      <div class="max-w-md w-full">
        <div class="card">
          <div class="text-center mb-8">
            <h1 class="text-3xl font-display font-bold text-gray-900">Welcome Back</h1>
            <p class="mt-2 text-gray-600">Sign in to continue your story journey</p>
          </div>

          <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="space-y-6">
            <mat-form-field appearance="outline" class="w-full">
              <mat-label>Email or Username</mat-label>
              <input matInput formControlName="username" autocomplete="username">
              <mat-icon matPrefix>person</mat-icon>
              <mat-error *ngIf="loginForm.get('username')?.hasError('required')">
                Username is required
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="w-full">
              <mat-label>Password</mat-label>
              <input matInput 
                     [type]="hidePassword() ? 'password' : 'text'" 
                     formControlName="password" 
                     autocomplete="current-password">
              <mat-icon matPrefix>lock</mat-icon>
              <button mat-icon-button matSuffix 
                      type="button"
                      (click)="hidePassword.set(!hidePassword())">
                <mat-icon>{{hidePassword() ? 'visibility_off' : 'visibility'}}</mat-icon>
              </button>
              <mat-error *ngIf="loginForm.get('password')?.hasError('required')">
                Password is required
              </mat-error>
            </mat-form-field>

            <div class="flex items-center justify-between">
              <a routerLink="/auth/forgot-password" 
                 class="text-sm text-primary-600 hover:text-primary-700">
                Forgot your password?
              </a>
            </div>

            <button mat-raised-button 
                    color="primary" 
                    type="submit"
                    class="w-full"
                    [disabled]="loginForm.invalid || isLoading()">
              <mat-spinner *ngIf="isLoading()" diameter="20" class="inline-block mr-2"></mat-spinner>
              {{ isLoading() ? 'Signing in...' : 'Sign In' }}
            </button>

            <div class="text-center">
              <span class="text-gray-600">Don't have an account?</span>
              <a routerLink="/auth/register" class="ml-1 text-primary-600 hover:text-primary-700 font-medium">
                Sign up
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `]
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private notification = inject(NotificationService);
  
  hidePassword = signal(true);
  isLoading = signal(false);
  
  loginForm: FormGroup = this.fb.group({
    username: ['', Validators.required],
    password: ['', Validators.required]
  });
  
  onSubmit(): void {
    if (this.loginForm.valid) {
      this.isLoading.set(true);
      
      this.authService.login(this.loginForm.value).subscribe({
        next: (user) => {
          this.notification.success('Welcome back!');
          const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
          this.router.navigate([returnUrl]);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.notification.error(error.error?.detail || 'Invalid credentials');
        },
        complete: () => this.isLoading.set(false)
      });
    }
  }
}
```

#### 3.3 Implement Register Component
```typescript
// src/app/features/auth/pages/register/register.component.ts
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, AbstractControl } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { AuthService } from '../../../../core/services/auth.service';
import { NotificationService } from '../../../../core/services/notification.service';

// Custom validator for password match
function passwordMatchValidator(control: AbstractControl): {[key: string]: any} | null {
  const password = control.get('password');
  const confirmPassword = control.get('confirmPassword');
  
  if (!password || !confirmPassword) {
    return null;
  }
  
  return password.value === confirmPassword.value ? null : { passwordMismatch: true };
}

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatCheckboxModule
  ],
  template: `
    <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4">
      <div class="max-w-md w-full">
        <div class="card">
          <div class="text-center mb-8">
            <h1 class="text-3xl font-display font-bold text-gray-900">Create Account</h1>
            <p class="mt-2 text-gray-600">Start creating amazing stories today</p>
          </div>

          <form [formGroup]="registerForm" (ngSubmit)="onSubmit()" class="space-y-6">
            <mat-form-field appearance="outline" class="w-full">
              <mat-label>Email</mat-label>
              <input matInput formControlName="email" type="email" autocomplete="email">
              <mat-icon matPrefix>email</mat-icon>
              <mat-error *ngIf="registerForm.get('email')?.hasError('required')">
                Email is required
              </mat-error>
              <mat-error *ngIf="registerForm.get('email')?.hasError('email')">
                Please enter a valid email
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="w-full">
              <mat-label>Username</mat-label>
              <input matInput formControlName="username" autocomplete="username">
              <mat-icon matPrefix>person</mat-icon>
              <mat-error *ngIf="registerForm.get('username')?.hasError('required')">
                Username is required
              </mat-error>
              <mat-error *ngIf="registerForm.get('username')?.hasError('minlength')">
                Username must be at least 3 characters
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="w-full">
              <mat-label>Password</mat-label>
              <input matInput 
                     [type]="hidePassword() ? 'password' : 'text'" 
                     formControlName="password" 
                     autocomplete="new-password">
              <mat-icon matPrefix>lock</mat-icon>
              <button mat-icon-button matSuffix 
                      type="button"
                      (click)="hidePassword.set(!hidePassword())">
                <mat-icon>{{hidePassword() ? 'visibility_off' : 'visibility'}}</mat-icon>
              </button>
              <mat-error *ngIf="registerForm.get('password')?.hasError('required')">
                Password is required
              </mat-error>
              <mat-error *ngIf="registerForm.get('password')?.hasError('minlength')">
                Password must be at least 8 characters
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="w-full">
              <mat-label>Confirm Password</mat-label>
              <input matInput 
                     [type]="hidePassword() ? 'password' : 'text'" 
                     formControlName="confirmPassword" 
                     autocomplete="new-password">
              <mat-icon matPrefix>lock</mat-icon>
              <mat-error *ngIf="registerForm.get('confirmPassword')?.hasError('required')">
                Please confirm your password
              </mat-error>
              <mat-error *ngIf="registerForm.hasError('passwordMismatch')">
                Passwords do not match
              </mat-error>
            </mat-form-field>

            <mat-checkbox formControlName="agreeToTerms" color="primary">
              I agree to the 
              <a href="/terms" target="_blank" class="text-primary-600 hover:text-primary-700">Terms of Service</a>
              and 
              <a href="/privacy" target="_blank" class="text-primary-600 hover:text-primary-700">Privacy Policy</a>
            </mat-checkbox>

            <button mat-raised-button 
                    color="primary" 
                    type="submit"
                    class="w-full"
                    [disabled]="registerForm.invalid || isLoading()">
              <mat-spinner *ngIf="isLoading()" diameter="20" class="inline-block mr-2"></mat-spinner>
              {{ isLoading() ? 'Creating Account...' : 'Create Account' }}
            </button>

            <div class="text-center">
              <span class="text-gray-600">Already have an account?</span>
              <a routerLink="/auth/login" class="ml-1 text-primary-600 hover:text-primary-700 font-medium">
                Sign in
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `]
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private notification = inject(NotificationService);
  
  hidePassword = signal(true);
  isLoading = signal(false);
  
  registerForm: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    username: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    confirmPassword: ['', Validators.required],
    agreeToTerms: [false, Validators.requiredTrue]
  }, { validators: passwordMatchValidator });
  
  onSubmit(): void {
    if (this.registerForm.valid) {
      this.isLoading.set(true);
      
      const { email, username, password } = this.registerForm.value;
      
      this.authService.register({ email, username, password }).subscribe({
        next: () => {
          this.notification.success('Account created successfully! Please log in.');
          this.router.navigate(['/auth/login']);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.notification.error(error.error?.detail || 'Registration failed');
        },
        complete: () => this.isLoading.set(false)
      });
    }
  }
}
```

### Step 4: Configure App Structure

#### 4.1 Update App Configuration
```typescript
// src/app/app.config.ts
import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideAnimations(),
    provideHttpClient(
      withInterceptors([authInterceptor, errorInterceptor])
    ),
  ]
};
```

#### 4.2 Configure App Routes
```typescript
// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard]
  },
  {
    path: 'characters',
    loadChildren: () => import('./features/characters/characters.routes').then(m => m.CHARACTER_ROUTES),
    canActivate: [authGuard]
  },
  {
    path: 'stories',
    loadChildren: () => import('./features/stories/stories.routes').then(m => m.STORY_ROUTES),
    canActivate: [authGuard]
  },
  {
    path: 'reader',
    loadChildren: () => import('./features/reader/reader.routes').then(m => m.READER_ROUTES),
    canActivate: [authGuard]
  },
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: '**',
    loadComponent: () => import('./shared/components/not-found/not-found.component').then(m => m.NotFoundComponent)
  }
];
```

## Week 2: Character Management Module

### Step 5: Create Character Models and Service

#### 5.1 Define Character Models
```typescript
// src/app/models/character.model.ts
export interface Trait {
  name: string;
  description: string;
}

export interface Character {
  id: string;
  name: string;
  optimized_name?: string;
  description: string;
  optimized_description?: string;
  traits: Trait[];
  optimized_traits?: Trait[];
  status: CharacterStatus;
  created_at?: string;
  updated_at?: string;
}

export enum CharacterStatus {
  DRAFT = 'draft',
  GENERATED = 'generated',
  FINALIZED = 'finalized'
}

export interface CharacterInput {
  name: string;
  description: string;
  traits: Trait[];
  story_context?: string;
}

export interface CharacterListResponse {
  characters: Character[];
  total: number;
  page: number;
  size: number;
}
```

#### 5.2 Implement Character Service
```typescript
// src/app/features/characters/services/character.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, tap, shareReplay } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Character, CharacterInput, CharacterStatus } from '../../../models/character.model';

@Injectable({
  providedIn: 'root'
})
export class CharacterService {
  private api = inject(ApiService);
  
  // Signals for state management
  private charactersSignal = signal<Character[]>([]);
  private selectedCharacterSignal = signal<Character | null>(null);
  private isLoadingSignal = signal(false);
  
  // Public readonly signals
  characters = this.charactersSignal.asReadonly();
  selectedCharacter = this.selectedCharacterSignal.asReadonly();
  isLoading = this.isLoadingSignal.asReadonly();
  
  // Computed values
  draftCharacters = computed(() => 
    this.charactersSignal().filter(c => c.status === CharacterStatus.DRAFT)
  );
  
  generatedCharacters = computed(() => 
    this.charactersSignal().filter(c => c.status === CharacterStatus.GENERATED)
  );
  
  finalizedCharacters = computed(() => 
    this.charactersSignal().filter(c => c.status === CharacterStatus.FINALIZED)
  );

  loadCharacters(status?: CharacterStatus): Observable<Character[]> {
    this.isLoadingSignal.set(true);
    
    const params = status ? { status } : {};
    
    return this.api.get<Character[]>('/characters/', params).pipe(
      tap(characters => {
        this.charactersSignal.set(characters);
        this.isLoadingSignal.set(false);
      }),
      shareReplay(1)
    );
  }

  getCharacter(id: string): Observable<Character> {
    return this.api.get<Character>(`/characters/${id}`).pipe(
      tap(character => this.selectedCharacterSignal.set(character))
    );
  }

  createCharacter(character: CharacterInput): Observable<Character> {
    return this.api.post<Character>('/characters/', character).pipe(
      tap(newCharacter => {
        this.charactersSignal.update(chars => [...chars, newCharacter]);
      })
    );
  }

  generateCharacter(id: string): Observable<Character> {
    this.isLoadingSignal.set(true);
    
    return this.api.post<Character>(`/characters/${id}/generate`).pipe(
      tap(updatedCharacter => {
        this.updateCharacterInList(updatedCharacter);
        this.selectedCharacterSignal.set(updatedCharacter);
        this.isLoadingSignal.set(false);
      })
    );
  }

  updateCharacter(id: string, updates: Partial<CharacterInput>): Observable<Character> {
    return this.api.put<Character>(`/characters/${id}/save`, updates).pipe(
      tap(updatedCharacter => {
        this.updateCharacterInList(updatedCharacter);
        this.selectedCharacterSignal.set(updatedCharacter);
      })
    );
  }

  finalizeCharacter(id: string): Observable<Character> {
    return this.api.post<Character>(`/characters/${id}/finalize`).pipe(
      tap(updatedCharacter => {
        this.updateCharacterInList(updatedCharacter);
        this.selectedCharacterSignal.set(updatedCharacter);
      })
    );
  }

  deleteCharacter(id: string): Observable<void> {
    return this.api.delete<void>(`/characters/${id}`).pipe(
      tap(() => {
        this.charactersSignal.update(chars => chars.filter(c => c.id !== id));
        if (this.selectedCharacterSignal()?.id === id) {
          this.selectedCharacterSignal.set(null);
        }
      })
    );
  }

  private updateCharacterInList(character: Character): void {
    this.charactersSignal.update(chars => 
      chars.map(c => c.id === character.id ? character : c)
    );
  }
}
```

### Step 6: Create Character Components

#### 6.1 Character List Component
```typescript
// src/app/features/characters/components/character-list/character-list.component.ts
import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { CharacterService } from '../../services/character.service';
import { Character, CharacterStatus } from '../../../../models/character.model';

@Component({
  selector: 'app-character-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    MatTooltipModule
  ],
  template: `
    <div class="container mx-auto px-4 py-8">
      <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-display font-bold text-gray-900">My Characters</h1>
        <a routerLink="/characters/create" mat-raised-button color="primary">
          <mat-icon>add</mat-icon>
          Create Character
        </a>
      </div>

      <mat-tab-group (selectedTabChange)="onTabChange($event)">
        <mat-tab label="All Characters">
          <ng-container *ngTemplateOutlet="characterGrid; context: { characters: characterService.characters() }">
          </ng-container>
        </mat-tab>
        <mat-tab label="Drafts">
          <ng-container *ngTemplateOutlet="characterGrid; context: { characters: characterService.draftCharacters() }">
          </ng-container>
        </mat-tab>
        <mat-tab label="Generated">
          <ng-container *ngTemplateOutlet="characterGrid; context: { characters: characterService.generatedCharacters() }">
          </ng-container>
        </mat-tab>
        <mat-tab label="Finalized">
          <ng-container *ngTemplateOutlet="characterGrid; context: { characters: characterService.finalizedCharacters() }">
          </ng-container>
        </mat-tab>
      </mat-tab-group>

      <!-- Character Grid Template -->
      <ng-template #characterGrid let-characters="characters">
        <div class="mt-6">
          <div *ngIf="characterService.isLoading()" class="text-center py-12">
            <mat-spinner></mat-spinner>
            <p class="mt-4 text-gray-600">Loading characters...</p>
          </div>

          <div *ngIf="!characterService.isLoading() && characters.length === 0" 
               class="text-center py-12">
            <mat-icon class="text-6xl text-gray-400">person_outline</mat-icon>
            <p class="mt-4 text-gray-600">No characters found</p>
            <a routerLink="/characters/create" mat-button color="primary" class="mt-2">
              Create your first character
            </a>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <mat-card *ngFor="let character of characters" 
                      class="hover:shadow-lg transition-shadow cursor-pointer"
                      [routerLink]="['/characters', character.id]">
              <mat-card-header>
                <mat-card-title class="text-xl font-semibold">
                  {{ character.optimized_name || character.name }}
                </mat-card-title>
                <mat-card-subtitle>
                  <mat-chip [color]="getStatusColor(character.status)" selected>
                    {{ character.status }}
                  </mat-chip>
                </mat-card-subtitle>
              </mat-card-header>

              <mat-card-content>
                <p class="text-gray-700 line-clamp-3">
                  {{ character.optimized_description || character.description }}
                </p>

                <div class="mt-4">
                  <h4 class="text-sm font-semibold text-gray-600 mb-2">Traits:</h4>
                  <div class="flex flex-wrap gap-2">
                    <mat-chip *ngFor="let trait of (character.optimized_traits || character.traits).slice(0, 3)"
                              [matTooltip]="trait.description">
                      {{ trait.name }}
                    </mat-chip>
                    <mat-chip *ngIf="(character.optimized_traits || character.traits).length > 3">
                      +{{ (character.optimized_traits || character.traits).length - 3 }} more
                    </mat-chip>
                  </div>
                </div>
              </mat-card-content>

              <mat-card-actions align="end">
                <button mat-button color="primary" 
                        [routerLink]="['/characters', character.id]"
                        (click)="$event.stopPropagation()">
                  <mat-icon>edit</mat-icon>
                  Edit
                </button>
                <button mat-button color="accent"
                        *ngIf="character.status === 'draft'"
                        (click)="generateCharacter($event, character.id)">
                  <mat-icon>auto_awesome</mat-icon>
                  Generate
                </button>
              </mat-card-actions>
            </mat-card>
          </div>
        </div>
      </ng-template>
    </div>
  `,
  styles: [`
    .line-clamp-3 {
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  `]
})
export class CharacterListComponent implements OnInit {
  characterService = inject(CharacterService);
  
  ngOnInit() {
    this.characterService.loadCharacters().subscribe();
  }

  onTabChange(event: any): void {
    const statusMap = ['', 'draft', 'generated', 'finalized'];
    const status = statusMap[event.index];
    
    if (status) {
      this.characterService.loadCharacters(status as CharacterStatus).subscribe();
    } else {
      this.characterService.loadCharacters().subscribe();
    }
  }

  getStatusColor(status: string): 'primary' | 'accent' | 'warn' {
    switch(status) {
      case 'draft': return 'warn';
      case 'generated': return 'accent';
      case 'finalized': return 'primary';
      default: return 'primary';
    }
  }

  generateCharacter(event: Event, id: string): void {
    event.stopPropagation();
    this.characterService.generateCharacter(id).subscribe();
  }
}
```

#### 6.2 Character Create/Edit Component
```typescript
// src/app/features/characters/components/character-form/character-form.component.ts
import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormArray, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';
import { MatStepperModule } from '@angular/material/stepper';
import { CharacterService } from '../../services/character.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Trait } from '../../../../models/character.model';

@Component({
  selector: 'app-character-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatCardModule,
    MatStepperModule
  ],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-4xl">
      <div class="mb-8">
        <h1 class="text-3xl font-display font-bold text-gray-900">
          {{ isEditMode() ? 'Edit Character' : 'Create New Character' }}
        </h1>
        <p class="mt-2 text-gray-600">
          Bring your character to life with rich details and personality traits
        </p>
      </div>

      <mat-card>
        <mat-card-content>
          <form [formGroup]="characterForm" (ngSubmit)="onSubmit()">
            <mat-stepper linear #stepper>
              <!-- Step 1: Basic Information -->
              <mat-step [stepControl]="characterForm.get('name')">
                <ng-template matStepLabel>Basic Information</ng-template>
                
                <div class="py-6 space-y-6">
                  <mat-form-field appearance="outline" class="w-full">
                    <mat-label>Character Name</mat-label>
                    <input matInput formControlName="name" placeholder="e.g., Captain Adventure">
                    <mat-error *ngIf="characterForm.get('name')?.hasError('required')">
                      Character name is required
                    </mat-error>
                  </mat-form-field>

                  <mat-form-field appearance="outline" class="w-full">
                    <mat-label>Description</mat-label>
                    <textarea matInput formControlName="description" 
                              rows="4"
                              placeholder="Describe your character's appearance, personality, and background..."></textarea>
                    <mat-hint align="end">{{ characterForm.get('description')?.value?.length || 0 }}/500</mat-hint>
                    <mat-error *ngIf="characterForm.get('description')?.hasError('required')">
                      Description is required
                    </mat-error>
                  </mat-form-field>

                  <mat-form-field appearance="outline" class="w-full">
                    <mat-label>Story Context (Optional)</mat-label>
                    <textarea matInput formControlName="story_context" 
                              rows="3"
                              placeholder="How does this character fit into your stories?"></textarea>
                  </mat-form-field>
                </div>

                <div class="flex justify-end gap-2">
                  <button mat-button matStepperNext type="button">
                    Next
                    <mat-icon>arrow_forward</mat-icon>
                  </button>
                </div>
              </mat-step>

              <!-- Step 2: Character Traits -->
              <mat-step>
                <ng-template matStepLabel>Character Traits</ng-template>
                
                <div class="py-6">
                  <div class="mb-4">
                    <h3 class="text-lg font-semibold mb-2">Add Character Traits</h3>
                    <p class="text-gray-600">Define the key traits that make your character unique</p>
                  </div>

                  <div formArrayName="traits" class="space-y-4">
                    <div *ngFor="let trait of traits.controls; let i = index" 
                         [formGroupName]="i"
                         class="bg-gray-50 p-4 rounded-lg">
                      <div class="flex gap-4">
                        <mat-form-field appearance="outline" class="flex-1">
                          <mat-label>Trait Name</mat-label>
                          <input matInput formControlName="name" placeholder="e.g., Brave">
                        </mat-form-field>

                        <mat-form-field appearance="outline" class="flex-2">
                          <mat-label>Trait Description</mat-label>
                          <input matInput formControlName="description" 
                                 placeholder="e.g., Never backs down from a challenge">
                        </mat-form-field>

                        <button mat-icon-button color="warn" 
                                type="button"
                                (click)="removeTrait(i)"
                                [disabled]="traits.length === 1">
                          <mat-icon>delete</mat-icon>
                        </button>
                      </div>
                    </div>
                  </div>

                  <button mat-button color="primary" type="button" (click)="addTrait()" class="mt-4">
                    <mat-icon>add</mat-icon>
                    Add Trait
                  </button>
                </div>

                <div class="flex justify-between gap-2">
                  <button mat-button matStepperPrevious type="button">
                    <mat-icon>arrow_back</mat-icon>
                    Back
                  </button>
                  <button mat-button matStepperNext type="button">
                    Next
                    <mat-icon>arrow_forward</mat-icon>
                  </button>
                </div>
              </mat-step>

              <!-- Step 3: Review & Submit -->
              <mat-step>
                <ng-template matStepLabel>Review & Create</ng-template>
                
                <div class="py-6">
                  <h3 class="text-lg font-semibold mb-4">Review Your Character</h3>
                  
                  <div class="bg-gray-50 p-6 rounded-lg space-y-4">
                    <div>
                      <h4 class="font-semibold text-gray-700">Name</h4>
                      <p>{{ characterForm.get('name')?.value }}</p>
                    </div>

                    <div>
                      <h4 class="font-semibold text-gray-700">Description</h4>
                      <p class="whitespace-pre-wrap">{{ characterForm.get('description')?.value }}</p>
                    </div>

                    <div *ngIf="characterForm.get('story_context')?.value">
                      <h4 class="font-semibold text-gray-700">Story Context</h4>
                      <p class="whitespace-pre-wrap">{{ characterForm.get('story_context')?.value }}</p>
                    </div>

                    <div>
                      <h4 class="font-semibold text-gray-700">Traits</h4>
                      <div class="flex flex-wrap gap-2 mt-2">
                        <mat-chip *ngFor="let trait of characterForm.get('traits')?.value">
                          {{ trait.name }}: {{ trait.description }}
                        </mat-chip>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="flex justify-between gap-2">
                  <button mat-button matStepperPrevious type="button">
                    <mat-icon>arrow_back</mat-icon>
                    Back
                  </button>
                  <button mat-raised-button 
                          color="primary" 
                          type="submit"
                          [disabled]="characterForm.invalid || isSubmitting()">
                    <mat-spinner *ngIf="isSubmitting()" diameter="20" class="inline-block mr-2"></mat-spinner>
                    {{ isEditMode() ? 'Update Character' : 'Create Character' }}
                  </button>
                </div>
              </mat-step>
            </mat-stepper>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
    
    .flex-2 {
      flex: 2;
    }
  `]
})
export class CharacterFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private characterService = inject(CharacterService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private notification = inject(NotificationService);
  
  isEditMode = signal(false);
  isSubmitting = signal(false);
  characterId = signal<string | null>(null);
  
  characterForm: FormGroup = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(100)]],
    description: ['', [Validators.required, Validators.maxLength(500)]],
    story_context: ['', Validators.maxLength(300)],
    traits: this.fb.array([this.createTraitGroup()])
  });
  
  get traits() {
    return this.characterForm.get('traits') as FormArray;
  }
  
  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditMode.set(true);
      this.characterId.set(id);
      this.loadCharacter(id);
    }
  }
  
  createTraitGroup(): FormGroup {
    return this.fb.group({
      name: ['', Validators.required],
      description: ['', Validators.required]
    });
  }
  
  addTrait(): void {
    this.traits.push(this.createTraitGroup());
  }
  
  removeTrait(index: number): void {
    if (this.traits.length > 1) {
      this.traits.removeAt(index);
    }
  }
  
  loadCharacter(id: string): void {
    this.characterService.getCharacter(id).subscribe({
      next: (character) => {
        this.characterForm.patchValue({
          name: character.name,
          description: character.description,
          story_context: character.story_context || ''
        });
        
        // Clear existing traits and add loaded ones
        while (this.traits.length > 0) {
          this.traits.removeAt(0);
        }
        
        character.traits.forEach(trait => {
          this.traits.push(this.fb.group({
            name: trait.name,
            description: trait.description
          }));
        });
      },
      error: () => {
        this.notification.error('Failed to load character');
        this.router.navigate(['/characters']);
      }
    });
  }
  
  onSubmit(): void {
    if (this.characterForm.valid) {
      this.isSubmitting.set(true);
      
      const characterData = this.characterForm.value;
      
      const request = this.isEditMode()
        ? this.characterService.updateCharacter(this.characterId()!, characterData)
        : this.characterService.createCharacter(characterData);
      
      request.subscribe({
        next: (character) => {
          this.notification.success(
            this.isEditMode() ? 'Character updated successfully' : 'Character created successfully'
          );
          this.router.navigate(['/characters', character.id]);
        },
        error: (error) => {
          this.isSubmitting.set(false);
          this.notification.error(error.error?.detail || 'Operation failed');
        }
      });
    }
  }
}
```

## Week 3: Story Creation Wizard

### Step 7: Story Models and Service

#### 7.1 Define Story Models
```typescript
// src/app/models/story.model.ts
import { Character } from './character.model';

export interface Story {
  id: string;
  title: string;
  optimized_title?: string;
  description: string;
  optimized_description?: string;
  character_ids: string[];
  character_roles?: CharacterRole[];
  content?: StoryContent;
  cover_image_id?: string;
  status: StoryStatus;
  scenes?: Scene[];
  target_audience?: string;
  genre?: string;
  total_reading_time?: number;
  total_word_count?: number;
  version?: number;
  refinement_count?: number;
}

export interface Scene {
  scene_id: string;
  scene_number: number;
  type: SceneType;
  title: string;
  content: string;
  image_prompt?: string;
  image_id?: string;
  characters_present: string[];
  estimated_reading_time: number;
  word_count: number;
}

export enum SceneType {
  INTRODUCTION = 'introduction',
  RISING_ACTION = 'rising_action',
  CLIMAX = 'climax',
  FALLING_ACTION = 'falling_action',
  CONCLUSION = 'conclusion'
}

export interface CharacterRole {
  name: string;
  role: string;
  enhanced_description: string;
  skills: Skill[];
  motivations: string;
  flaws: string;
  interactions: string;
}

export interface Skill {
  skill_name: string;
  skill_description: string;
}

export interface StoryContent {
  story_structure: StoryStructure;
  full_story: string;
}

export interface StoryStructure {
  introduction: string;
  middle: MiddleSection;
  climax: string;
  conclusion: string;
  lessons: string[];
}

export interface MiddleSection {
  setting_out: string;
  encounter_with_challenges: string;
  tests: Test[];
}

export interface Test {
  test_name: string;
  description: string;
}

export enum StoryStatus {
  DRAFT = 'draft',
  GENERATED = 'generated',
  FINALIZED = 'finalized',
  PUBLISHED = 'published',
  ARCHIVED = 'archived'
}

export interface StoryInput {
  title: string;
  description: string;
  character_ids: string[];
  target_audience?: string;
  genre?: string;
}

export interface RefinementRequest {
  refinement_type: RefinementType;
  custom_instructions?: string;
  preserve_elements?: string[];
  target_length?: 'shorter' | 'same' | 'longer';
}

export enum RefinementType {
  SIMPLIFY_LANGUAGE = 'simplify_language',
  ADD_MORE_ACTION = 'add_more_action',
  INCREASE_DIALOGUE = 'increase_dialogue',
  ENHANCE_DESCRIPTIONS = 'enhance_descriptions',
  STRENGTHEN_MORAL = 'strengthen_moral',
  ADD_HUMOR = 'add_humor',
  INCREASE_SUSPENSE = 'increase_suspense',
  CUSTOM = 'custom'
}
```

#### 7.2 Implement Story Service
```typescript
// src/app/features/stories/services/story.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, tap, shareReplay } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Story, StoryInput, StoryStatus, RefinementRequest } from '../../../models/story.model';

@Injectable({
  providedIn: 'root'
})
export class StoryService {
  private api = inject(ApiService);
  
  // Signals for state management
  private storiesSignal = signal<Story[]>([]);
  private selectedStorySignal = signal<Story | null>(null);
  private isLoadingSignal = signal(false);
  private generationProgressSignal = signal<number>(0);
  
  // Public readonly signals
  stories = this.storiesSignal.asReadonly();
  selectedStory = this.selectedStorySignal.asReadonly();
  isLoading = this.isLoadingSignal.asReadonly();
  generationProgress = this.generationProgressSignal.asReadonly();
  
  // Computed values
  draftStories = computed(() => 
    this.storiesSignal().filter(s => s.status === StoryStatus.DRAFT)
  );
  
  publishedStories = computed(() => 
    this.storiesSignal().filter(s => s.status === StoryStatus.PUBLISHED)
  );

  loadStories(status?: StoryStatus): Observable<Story[]> {
    this.isLoadingSignal.set(true);
    
    const params = status ? { status } : {};
    
    return this.api.get<Story[]>('/stories/', params).pipe(
      tap(stories => {
        this.storiesSignal.set(stories);
        this.isLoadingSignal.set(false);
      }),
      shareReplay(1)
    );
  }

  getStory(id: string): Observable<Story> {
    return this.api.get<Story>(`/stories/${id}`).pipe(
      tap(story => this.selectedStorySignal.set(story))
    );
  }

  createStory(story: StoryInput): Observable<Story> {
    return this.api.post<Story>('/stories/', story).pipe(
      tap(newStory => {
        this.storiesSignal.update(stories => [...stories, newStory]);
      })
    );
  }

  generateStoryContent(id: string): Observable<Story> {
    this.isLoadingSignal.set(true);
    this.generationProgressSignal.set(0);
    
    // Simulate progress updates
    const progressInterval = setInterval(() => {
      this.generationProgressSignal.update(p => Math.min(p + 10, 90));
    }, 1000);
    
    return this.api.post<Story>(`/stories/${id}/content`).pipe(
      tap(updatedStory => {
        clearInterval(progressInterval);
        this.generationProgressSignal.set(100);
        this.updateStoryInList(updatedStory);
        this.selectedStorySignal.set(updatedStory);
        this.isLoadingSignal.set(false);
        
        // Reset progress after animation
        setTimeout(() => this.generationProgressSignal.set(0), 500);
      })
    );
  }

  refineStory(id: string): Observable<Story> {
    return this.api.post<Story>(`/stories/${id}/refine`).pipe(
      tap(updatedStory => {
        this.updateStoryInList(updatedStory);
        this.selectedStorySignal.set(updatedStory);
      })
    );
  }

  refineScene(storyId: string, sceneId: string, request: RefinementRequest): Observable<any> {
    return this.api.post(`/stories/${storyId}/refine-scene/${sceneId}`, request).pipe(
      tap(() => this.getStory(storyId).subscribe())
    );
  }

  generateSceneImages(id: string): Observable<any> {
    return this.api.post(`/stories/${id}/generate-scene-images`);
  }

  generateCoverImage(id: string): Observable<any> {
    return this.api.post(`/stories/${id}/cover_image`);
  }

  updateStory(id: string, updates: Partial<StoryInput>): Observable<Story> {
    return this.api.put<Story>(`/stories/${id}/update`, updates).pipe(
      tap(updatedStory => {
        this.updateStoryInList(updatedStory);
        this.selectedStorySignal.set(updatedStory);
      })
    );
  }

  deleteStory(id: string): Observable<void> {
    return this.api.delete<void>(`/stories/${id}`).pipe(
      tap(() => {
        this.storiesSignal.update(stories => stories.filter(s => s.id !== id));
        if (this.selectedStorySignal()?.id === id) {
          this.selectedStorySignal.set(null);
        }
      })
    );
  }

  exportStory(id: string, format: 'pdf' | 'markdown' | 'epub'): Observable<Blob> {
    return this.api.get<Blob>(`/stories/${id}/export/${format}`, {
      responseType: 'blob' as any
    });
  }

  private updateStoryInList(story: Story): void {
    this.storiesSignal.update(stories => 
      stories.map(s => s.id === story.id ? story : s)
    );
  }
}
```

### Step 8: Create Story Creation Wizard

#### 8.1 Story Creation Wizard Component
```typescript
// src/app/features/stories/components/story-wizard/story-wizard.component.ts
import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatStepperModule } from '@angular/material/stepper';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { CharacterService } from '../../../characters/services/character.service';
import { StoryService } from '../../services/story.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Character, CharacterStatus } from '../../../../models/character.model';

interface AudienceOption {
  value: string;
  label: string;
  description: string;
}

interface GenreOption {
  value: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-story-wizard',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatStepperModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatChipsModule,
    MatProgressBarModule,
    MatCheckboxModule
  ],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-5xl">
      <div class="mb-8 text-center">
        <h1 class="text-4xl font-display font-bold text-gray-900">Create Your Story</h1>
        <p class="mt-2 text-lg text-gray-600">
          Bring your characters to life in an amazing adventure
        </p>
      </div>

      <mat-stepper linear #stepper class="shadow-lg rounded-lg">
        <!-- Step 1: Story Basics -->
        <mat-step [stepControl]="basicInfoForm">
          <ng-template matStepLabel>Story Basics</ng-template>
          
          <form [formGroup]="basicInfoForm" class="p-8">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <mat-form-field appearance="outline" class="w-full">
                <mat-label>Story Title</mat-label>
                <input matInput formControlName="title" 
                       placeholder="e.g., The Magical Forest Adventure">
                <mat-error *ngIf="basicInfoForm.get('title')?.hasError('required')">
                  Title is required
                </mat-error>
              </mat-form-field>

              <mat-form-field appearance="outline" class="w-full">
                <mat-label>Target Audience</mat-label>
                <mat-select formControlName="target_audience">
                  <mat-option *ngFor="let audience of audienceOptions" 
                              [value]="audience.value">
                    <span class="font-semibold">{{ audience.label }}</span>
                    <br>
                    <small class="text-gray-600">{{ audience.description }}</small>
                  </mat-option>
                </mat-select>
              </mat-form-field>
            </div>

            <mat-form-field appearance="outline" class="w-full mt-6">
              <mat-label>Story Description</mat-label>
              <textarea matInput formControlName="description" rows="4"
                        placeholder="What's your story about? Set the scene and describe the adventure..."></textarea>
              <mat-hint align="end">{{ basicInfoForm.get('description')?.value?.length || 0 }}/500</mat-hint>
              <mat-error *ngIf="basicInfoForm.get('description')?.hasError('required')">
                Description is required
              </mat-error>
            </mat-form-field>

            <div class="mt-6">
              <label class="block text-sm font-medium text-gray-700 mb-3">Select Genre</label>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <mat-card *ngFor="let genre of genreOptions" 
                          class="cursor-pointer transition-all"
                          [class.ring-2]="basicInfoForm.get('genre')?.value === genre.value"
                          [class.ring-primary-500]="basicInfoForm.get('genre')?.value === genre.value"
                          (click)="selectGenre(genre.value)">
                  <mat-card-content class="text-center py-4">
                    <mat-icon class="text-3xl mb-2">{{ genre.icon }}</mat-icon>
                    <p class="font-semibold">{{ genre.label }}</p>
                  </mat-card-content>
                </mat-card>
              </div>
            </div>

            <div class="flex justify-end mt-8">
              <button mat-raised-button color="primary" matStepperNext
                      [disabled]="basicInfoForm.invalid">
                Next
                <mat-icon>arrow_forward</mat-icon>
              </button>
            </div>
          </form>
        </mat-step>

        <!-- Step 2: Select Characters -->
        <mat-step [stepControl]="characterForm">
          <ng-template matStepLabel>Choose Characters</ng-template>
          
          <form [formGroup]="characterForm" class="p-8">
            <div class="mb-6">
              <h3 class="text-xl font-semibold mb-2">Select Your Characters</h3>
              <p class="text-gray-600">Choose at least 2 characters for your story</p>
            </div>

            <div *ngIf="availableCharacters().length === 0" class="text-center py-12">
              <mat-icon class="text-6xl text-gray-400">person_outline</mat-icon>
              <p class="mt-4 text-gray-600">No characters available</p>
              <p class="text-sm text-gray-500 mt-2">
                You need at least 2 generated or finalized characters to create a story
              </p>
              <button mat-raised-button color="primary" 
                      routerLink="/characters/create" class="mt-4">
                Create Characters
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <mat-card *ngFor="let character of availableCharacters()" 
                        class="cursor-pointer transition-all"
                        [class.ring-2]="isCharacterSelected(character.id)"
                        [class.ring-primary-500]="isCharacterSelected(character.id)"
                        (click)="toggleCharacter(character.id)">
                <mat-card-header>
                  <mat-card-title>
                    {{ character.optimized_name || character.name }}
                  </mat-card-title>
                  <mat-card-subtitle>
                    <mat-chip [color]="character.status === 'finalized' ? 'primary' : 'accent'" selected>
                      {{ character.status }}
                    </mat-chip>
                  </mat-card-subtitle>
                </mat-card-header>
                <mat-card-content>
                  <p class="text-sm text-gray-700 line-clamp-2">
                    {{ character.optimized_description || character.description }}
                  </p>
                  <div class="mt-3 flex flex-wrap gap-1">
                    <mat-chip *ngFor="let trait of (character.optimized_traits || character.traits).slice(0, 2)"
                              size="small">
                      {{ trait.name }}
                    </mat-chip>
                  </div>
                </mat-card-content>
                <mat-card-actions>
                  <mat-checkbox [checked]="isCharacterSelected(character.id)"
                                (click)="$event.stopPropagation()">
                    Select
                  </mat-checkbox>
                </mat-card-actions>
              </mat-card>
            </div>

            <div class="flex justify-between mt-8">
              <button mat-button matStepperPrevious>
                <mat-icon>arrow_back</mat-icon>
                Back
              </button>
              <button mat-raised-button color="primary" matStepperNext
                      [disabled]="selectedCharacterIds().length < 2">
                Next ({{ selectedCharacterIds().length }} selected)
                <mat-icon>arrow_forward</mat-icon>
              </button>
            </div>
          </form>
        </mat-step>

        <!-- Step 3: Review & Generate -->
        <mat-step>
          <ng-template matStepLabel>Review & Generate</ng-template>
          
          <div class="p-8">
            <h3 class="text-xl font-semibold mb-6">Review Your Story Setup</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-4">
                <div>
                  <h4 class="font-semibold text-gray-700">Title</h4>
                  <p class="text-lg">{{ basicInfoForm.get('title')?.value }}</p>
                </div>
                
                <div>
                  <h4 class="font-semibold text-gray-700">Description</h4>
                  <p class="text-gray-600">{{ basicInfoForm.get('description')?.value }}</p>
                </div>
                
                <div>
                  <h4 class="font-semibold text-gray-700">Target Audience</h4>
                  <p>{{ getAudienceLabel(basicInfoForm.get('target_audience')?.value) }}</p>
                </div>
                
                <div>
                  <h4 class="font-semibold text-gray-700">Genre</h4>
                  <p>{{ getGenreLabel(basicInfoForm.get('genre')?.value) }}</p>
                </div>
              </div>
              
              <div>
                <h4 class="font-semibold text-gray-700 mb-3">Selected Characters</h4>
                <div class="space-y-2">
                  <mat-card *ngFor="let char of getSelectedCharacters()" class="p-3">
                    <h5 class="font-semibold">{{ char.optimized_name || char.name }}</h5>
                    <p class="text-sm text-gray-600 line-clamp-2">
                      {{ char.optimized_description || char.description }}
                    </p>
                  </mat-card>
                </div>
              </div>
            </div>

            <div *ngIf="generationProgress() > 0" class="mt-8">
              <h4 class="font-semibold mb-2">Generating Your Story...</h4>
              <mat-progress-bar [value]="generationProgress()" mode="determinate"></mat-progress-bar>
              <p class="text-sm text-gray-600 mt-2">
                {{ getProgressMessage() }}
              </p>
            </div>

            <div class="flex justify-between mt-8">
              <button mat-button matStepperPrevious [disabled]="isCreating()">
                <mat-icon>arrow_back</mat-icon>
                Back
              </button>
              <button mat-raised-button color="primary" 
                      (click)="createStory()"
                      [disabled]="isCreating()">
                <mat-icon *ngIf="!isCreating()">auto_awesome</mat-icon>
                {{ isCreating() ? 'Creating Story...' : 'Create Story' }}
              </button>
            </div>
          </div>
        </mat-step>
      </mat-stepper>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
    
    .line-clamp-2 {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  `]
})
export class StoryWizardComponent implements OnInit {
  private fb = inject(FormBuilder);
  private characterService = inject(CharacterService);
  private storyService = inject(StoryService);
  private router = inject(Router);
  private notification = inject(NotificationService);
  
  isCreating = signal(false);
  selectedCharacterIds = signal<string[]>([]);
  generationProgress = computed(() => this.storyService.generationProgress());
  
  basicInfoForm: FormGroup = this.fb.group({
    title: ['', [Validators.required, Validators.maxLength(100)]],
    description: ['', [Validators.required, Validators.maxLength(500)]],
    target_audience: ['children_6_10', Validators.required],
    genre: ['adventure', Validators.required]
  });
  
  characterForm: FormGroup = this.fb.group({
    character_ids: [[], [Validators.required, Validators.minLength(2)]]
  });
  
  audienceOptions: AudienceOption[] = [
    { value: 'toddlers_2_4', label: 'Toddlers (2-4)', description: 'Simple stories with basic concepts' },
    { value: 'children_5_7', label: 'Young Children (5-7)', description: 'Fun adventures with clear morals' },
    { value: 'children_8_10', label: 'Middle Grade (8-10)', description: 'Complex plots with character growth' },
    { value: 'preteens_11_13', label: 'Preteens (11-13)', description: 'Deeper themes and relationships' },
    { value: 'ya_14_17', label: 'Young Adults (14-17)', description: 'Mature themes and nuanced stories' },
    { value: 'adults_18_plus', label: 'Adults (18+)', description: 'Sophisticated narratives' }
  ];
  
  genreOptions: GenreOption[] = [
    { value: 'adventure', label: 'Adventure', icon: 'explore' },
    { value: 'fantasy', label: 'Fantasy', icon: 'auto_awesome' },
    { value: 'mystery', label: 'Mystery', icon: 'search' },
    { value: 'educational', label: 'Educational', icon: 'school' },
    { value: 'comedy', label: 'Comedy', icon: 'sentiment_very_satisfied' },
    { value: 'drama', label: 'Drama', icon: 'theater_comedy' }
  ];
  
  availableCharacters = computed(() => {
    return this.characterService.characters().filter(
      c => c.status === CharacterStatus.GENERATED || c.status === CharacterStatus.FINALIZED
    );
  });
  
  ngOnInit() {
    this.characterService.loadCharacters().subscribe();
    
    // Sync character selection with form
    this.selectedCharacterIds.asReadonly().subscribe(ids => {
      this.characterForm.patchValue({ character_ids: ids });
    });
  }
  
  selectGenre(genre: string): void {
    this.basicInfoForm.patchValue({ genre });
  }
  
  toggleCharacter(characterId: string): void {
    this.selectedCharacterIds.update(ids => {
      const index = ids.indexOf(characterId);
      if (index > -1) {
        return ids.filter(id => id !== characterId);
      } else {
        return [...ids, characterId];
      }
    });
  }
  
  isCharacterSelected(characterId: string): boolean {
    return this.selectedCharacterIds().includes(characterId);
  }
  
  getSelectedCharacters(): Character[] {
    return this.availableCharacters().filter(
      c => this.selectedCharacterIds().includes(c.id)
    );
  }
  
  getAudienceLabel(value: string): string {
    return this.audienceOptions.find(a => a.value === value)?.label || value;
  }
  
  getGenreLabel(value: string): string {
    return this.genreOptions.find(g => g.value === value)?.label || value;
  }
  
  getProgressMessage(): string {
    const progress = this.generationProgress();
    if (progress < 30) return 'Setting up your story world...';
    if (progress < 60) return 'Developing character interactions...';
    if (progress < 90) return 'Crafting the perfect adventure...';
    return 'Finalizing your masterpiece...';
  }
  
  createStory(): void {
    if (this.basicInfoForm.valid && this.characterForm.valid) {
      this.isCreating.set(true);
      
      const storyData = {
        ...this.basicInfoForm.value,
        character_ids: this.selectedCharacterIds()
      };
      
      // First create the story
      this.storyService.createStory(storyData).subscribe({
        next: (story) => {
          // Then generate content
          this.storyService.generateStoryContent(story.id).subscribe({
            next: (generatedStory) => {
              this.notification.success('Story created successfully!');
              this.router.navigate(['/stories', generatedStory.id]);
            },
            error: (error) => {
              this.isCreating.set(false);
              this.notification.error('Failed to generate story content');
            }
          });
        },
        error: (error) => {
          this.isCreating.set(false);
          this.notification.error(error.error?.detail || 'Failed to create story');
        }
      });
    }
  }
}
```

## Week 4: Basic Story Reader

### Step 9: Story Reader Component

#### 9.1 Story Reader Implementation
```typescript
// src/app/features/reader/components/story-reader/story-reader.component.ts
import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatMenuModule } from '@angular/material/menu';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { StoryService } from '../../../stories/services/story.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Story, Scene } from '../../../../models/story.model';
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-story-reader',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatChipsModule,
    MatMenuModule,
    MatSlideToggleModule
  ],
  animations: [
    trigger('sceneTransition', [
      transition(':increment', [
        style({ transform: 'translateX(100%)', opacity: 0 }),
        animate('600ms ease-out', style({ transform: 'translateX(0%)', opacity: 1 }))
      ]),
      transition(':decrement', [
        style({ transform: 'translateX(-100%)', opacity: 0 }),
        animate('600ms ease-out', style({ transform: 'translateX(0%)', opacity: 1 }))
      ])
    ])
  ],
  template: `
    <div class="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <!-- Header -->
      <header class="sticky top-0 z-10 bg-white shadow-sm">
        <div class="container mx-auto px-4 py-4">
          <div class="flex items-center justify-between">
            <button mat-icon-button (click)="goBack()">
              <mat-icon>arrow_back</mat-icon>
            </button>
            
            <h1 class="text-xl font-display font-semibold text-gray-900 text-center flex-1">
              {{ story()?.optimized_title || story()?.title }}
            </h1>
            
            <button mat-icon-button [matMenuTriggerFor]="menu">
              <mat-icon>more_vert</mat-icon>
            </button>
            <mat-menu #menu="matMenu">
              <button mat-menu-item (click)="toggleReadingMode()">
                <mat-icon>{{ isNightMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
                {{ isNightMode() ? 'Day Mode' : 'Night Mode' }}
              </button>
              <button mat-menu-item (click)="adjustFontSize('increase')">
                <mat-icon>text_increase</mat-icon>
                Increase Font Size
              </button>
              <button mat-menu-item (click)="adjustFontSize('decrease')">
                <mat-icon>text_decrease</mat-icon>
                Decrease Font Size
              </button>
              <button mat-menu-item (click)="shareStory()">
                <mat-icon>share</mat-icon>
                Share Story
              </button>
            </mat-menu>
          </div>
          
          <!-- Progress Bar -->
          <mat-progress-bar 
            [value]="readingProgress()" 
            mode="determinate"
            class="mt-2">
          </mat-progress-bar>
        </div>
      </header>

      <!-- Main Content -->
      <main class="container mx-auto px-4 py-8 max-w-4xl" 
            [class.night-mode]="isNightMode()">
        <div *ngIf="!story()" class="text-center py-12">
          <mat-spinner></mat-spinner>
          <p class="mt-4 text-gray-600">Loading story...</p>
        </div>

        <div *ngIf="story() && currentScene()" [@sceneTransition]="currentSceneIndex()">
          <!-- Scene Content -->
          <mat-card class="story-card" [style.font-size.px]="fontSize()">
            <!-- Scene Image -->
            <div *ngIf="currentScene()?.image_id" class="mb-6">
              <img [src]="getSceneImageUrl(currentScene()!.image_id)" 
                   [alt]="currentScene()!.title"
                   class="w-full h-auto rounded-lg shadow-lg">
            </div>

            <!-- Scene Title -->
            <h2 class="text-2xl md:text-3xl font-display font-bold mb-4 text-center"
                [style.font-size.px]="fontSize() + 8">
              {{ currentScene()!.title }}
            </h2>

            <!-- Scene Content -->
            <div class="prose prose-lg max-w-none story-content"
                 [innerHTML]="formatSceneContent(currentScene()!.content)">
            </div>

            <!-- Scene Metadata -->
            <div class="mt-6 flex items-center justify-between text-sm text-gray-500">
              <span>
                Scene {{ currentSceneIndex() + 1 }} of {{ totalScenes() }}
              </span>
              <span>
                <mat-icon class="text-base align-middle">schedule</mat-icon>
                {{ Math.ceil(currentScene()!.estimated_reading_time / 60) }} min read
              </span>
            </div>
          </mat-card>

          <!-- Navigation Controls -->
          <div class="flex justify-between items-center mt-8">
            <button mat-raised-button 
                    (click)="previousScene()"
                    [disabled]="currentSceneIndex() === 0">
              <mat-icon>chevron_left</mat-icon>
              Previous
            </button>

            <!-- Scene Selector -->
            <div class="flex items-center gap-2">
              <button *ngFor="let scene of story()?.scenes; let i = index"
                      mat-icon-button
                      [color]="i === currentSceneIndex() ? 'primary' : ''"
                      (click)="goToScene(i)"
                      [matTooltip]="scene.title">
                <mat-icon>{{ getSceneIcon(scene.type) }}</mat-icon>
              </button>
            </div>

            <button mat-raised-button 
                    color="primary"
                    (click)="nextScene()"
                    [disabled]="currentSceneIndex() === totalScenes() - 1">
              Next
              <mat-icon>chevron_right</mat-icon>
            </button>
          </div>

          <!-- Story Complete Message -->
          <div *ngIf="isLastScene()" class="mt-12 text-center">
            <mat-card class="bg-primary-50 border-primary-200">
              <mat-card-content class="py-8">
                <mat-icon class="text-6xl text-primary-600">auto_stories</mat-icon>
                <h3 class="text-2xl font-display font-bold mt-4 mb-2">Story Complete!</h3>
                <p class="text-gray-700 mb-6">
                  Thank you for reading "{{ story()?.title }}"
                </p>
                
                <div *ngIf="story()?.content?.story_structure?.lessons?.length" class="mb-6">
                  <h4 class="font-semibold mb-2">Lessons Learned:</h4>
                  <ul class="text-left max-w-md mx-auto">
                    <li *ngFor="let lesson of story()!.content!.story_structure.lessons" 
                        class="mb-1">
                      • {{ lesson }}
                    </li>
                  </ul>
                </div>
                
                <div class="flex gap-4 justify-center">
                  <button mat-raised-button (click)="goToScene(0)">
                    <mat-icon>replay</mat-icon>
                    Read Again
                  </button>
                  <button mat-raised-button color="primary" routerLink="/stories">
                    <mat-icon>library_books</mat-icon>
                    More Stories
                  </button>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </div>
      </main>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
    
    .story-card {
      padding: 2rem;
      line-height: 1.8;
    }
    
    .story-content {
      font-family: 'Georgia', serif;
    }
    
    .night-mode {
      background-color: #1a1a1a;
      color: #e0e0e0;
    }
    
    .night-mode .story-card {
      background-color: #2a2a2a;
      color: #e0e0e0;
    }
    
    .night-mode .prose {
      color: #e0e0e0;
    }
    
    @media (max-width: 768px) {
      .story-card {
        padding: 1rem;
      }
    }
  `]
})
export class StoryReaderComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private storyService = inject(StoryService);
  private notification = inject(NotificationService);
  
  // State signals
  story = signal<Story | null>(null);
  currentSceneIndex = signal(0);
  isNightMode = signal(false);
  fontSize = signal(18);
  
  // Computed values
  currentScene = computed(() => {
    const s = this.story();
    const index = this.currentSceneIndex();
    return s?.scenes?.[index] || null;
  });
  
  totalScenes = computed(() => this.story()?.scenes?.length || 0);
  
  readingProgress = computed(() => {
    const current = this.currentSceneIndex() + 1;
    const total = this.totalScenes();
    return total > 0 ? (current / total) * 100 : 0;
  });
  
  isLastScene = computed(() => 
    this.currentSceneIndex() === this.totalScenes() - 1
  );
  
  ngOnInit() {
    const storyId = this.route.snapshot.paramMap.get('id');
    if (storyId) {
      this.loadStory(storyId);
    } else {
      this.notification.error('Invalid story ID');
      this.router.navigate(['/stories']);
    }
    
    // Load saved preferences
    this.loadReadingPreferences();
  }
  
  loadStory(id: string): void {
    this.storyService.getStory(id).subscribe({
      next: (story) => {
        if (!story.scenes || story.scenes.length === 0) {
          this.notification.error('This story has no content yet');
          this.router.navigate(['/stories', id]);
        } else {
          this.story.set(story);
          // Load saved reading position
          this.loadReadingPosition(id);
        }
      },
      error: () => {
        this.notification.error('Failed to load story');
        this.router.navigate(['/stories']);
      }
    });
  }
  
  previousScene(): void {
    if (this.currentSceneIndex() > 0) {
      this.currentSceneIndex.update(i => i - 1);
      this.saveReadingPosition();
      window.scrollTo(0, 0);
    }
  }
  
  nextScene(): void {
    if (this.currentSceneIndex() < this.totalScenes() - 1) {
      this.currentSceneIndex.update(i => i + 1);
      this.saveReadingPosition();
      window.scrollTo(0, 0);
    }
  }
  
  goToScene(index: number): void {
    if (index >= 0 && index < this.totalScenes()) {
      this.currentSceneIndex.set(index);
      this.saveReadingPosition();
      window.scrollTo(0, 0);
    }
  }
  
  toggleReadingMode(): void {
    this.isNightMode.update(mode => !mode);
    this.saveReadingPreferences();
  }
  
  adjustFontSize(action: 'increase' | 'decrease'): void {
    if (action === 'increase' && this.fontSize() < 32) {
      this.fontSize.update(size => size + 2);
    } else if (action === 'decrease' && this.fontSize() > 12) {
      this.fontSize.update(size => size - 2);
    }
    this.saveReadingPreferences();
  }
  
  formatSceneContent(content: string): string {
    // Convert line breaks to paragraphs
    return content
      .split('\n\n')
      .map(para => `<p class="mb-4">${para}</p>`)
      .join('');
  }
  
  getSceneIcon(type: string): string {
    const iconMap: { [key: string]: string } = {
      'introduction': 'bookmark_border',
      'rising_action': 'trending_up',
      'climax': 'star',
      'falling_action': 'trending_down',
      'conclusion': 'bookmark'
    };
    return iconMap[type] || 'circle';
  }
  
  getSceneImageUrl(imageId: string): string {
    // This would be replaced with actual image URL logic
    return `/api/images/${imageId}`;
  }
  
  shareStory(): void {
    if (navigator.share) {
      navigator.share({
        title: this.story()?.title,
        text: this.story()?.description,
        url: window.location.href
      });
    } else {
      // Fallback - copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      this.notification.success('Story link copied to clipboard!');
    }
  }
  
  goBack(): void {
    this.router.navigate(['/stories', this.story()?.id]);
  }
  
  private saveReadingPosition(): void {
    if (this.story()?.id) {
      localStorage.setItem(
        `reading_position_${this.story()!.id}`,
        this.currentSceneIndex().toString()
      );
    }
  }
  
  private loadReadingPosition(storyId: string): void {
    const savedPosition = localStorage.getItem(`reading_position_${storyId}`);
    if (savedPosition) {
      const position = parseInt(savedPosition, 10);
      if (!isNaN(position) && position < this.totalScenes()) {
        this.currentSceneIndex.set(position);
      }
    }
  }
  
  private saveReadingPreferences(): void {
    localStorage.setItem('reading_preferences', JSON.stringify({
      nightMode: this.isNightMode(),
      fontSize: this.fontSize()
    }));
  }
  
  private loadReadingPreferences(): void {
    const saved = localStorage.getItem('reading_preferences');
    if (saved) {
      try {
        const prefs = JSON.parse(saved);
        this.isNightMode.set(prefs.nightMode || false);
        this.fontSize.set(prefs.fontSize || 18);
      } catch (e) {
        console.error('Failed to load reading preferences');
      }
    }
  }
}
```

### Step 10: Configure Module Routes

#### 10.1 Auth Routes
```typescript
// src/app/features/auth/auth.routes.ts
import { Routes } from '@angular/router';

export const AUTH_ROUTES: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'register',
    loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent)
  },
  {
    path: 'forgot-password',
    loadComponent: () => import('./pages/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
  },
  {
    path: 'reset-password',
    loadComponent: () => import('./pages/reset-password/reset-password.component').then(m => m.ResetPasswordComponent)
  },
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  }
];
```

#### 10.2 Character Routes
```typescript
// src/app/features/characters/characters.routes.ts
import { Routes } from '@angular/router';

export const CHARACTER_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./components/character-list/character-list.component').then(m => m.CharacterListComponent)
  },
  {
    path: 'create',
    loadComponent: () => import('./components/character-form/character-form.component').then(m => m.CharacterFormComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./components/character-detail/character-detail.component').then(m => m.CharacterDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./components/character-form/character-form.component').then(m => m.CharacterFormComponent)
  }
];
```

#### 10.3 Story Routes
```typescript
// src/app/features/stories/stories.routes.ts
import { Routes } from '@angular/router';

export const STORY_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./components/story-list/story-list.component').then(m => m.StoryListComponent)
  },
  {
    path: 'create',
    loadComponent: () => import('./components/story-wizard/story-wizard.component').then(m => m.StoryWizardComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./components/story-detail/story-detail.component').then(m => m.StoryDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./components/story-edit/story-edit.component').then(m => m.StoryEditComponent)
  }
];
```

#### 10.4 Reader Routes
```typescript
// src/app/features/reader/reader.routes.ts
import { Routes } from '@angular/router';

export const READER_ROUTES: Routes = [
  {
    path: ':id',
    loadComponent: () => import('./components/story-reader/story-reader.component').then(m => m.StoryReaderComponent)
  }
];
```

## Deployment & Testing

### Development Server
```bash
# Start the development server
ng serve

# With specific configuration
ng serve --configuration=development --port=4200 --open
```

### Building for Production
```bash
# Build for production
ng build --configuration=production

# Build with stats for bundle analysis
ng build --configuration=production --stats-json
```

### Testing Setup
```bash
# Install testing dependencies
npm install --save-dev @angular-devkit/build-angular karma karma-chrome-launcher karma-jasmine karma-jasmine-html-reporter jasmine-core @types/jasmine

# Run unit tests
ng test

# Run e2e tests with Cypress
npm install --save-dev cypress @cypress/schematic
ng add @cypress/schematic
ng e2e
```

### Environment Configuration
```typescript
// angular.json - update for API proxy in development
{
  "serve": {
    "builder": "@angular-devkit/build-angular:dev-server",
    "options": {
      "browserTarget": "genstory-frontend:build",
      "proxyConfig": "proxy.conf.json"
    }
  }
}

// proxy.conf.json
{
  "/api/*": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true,
    "logLevel": "debug"
  }
}
```

## Best Practices & Tips

### 1. Performance Optimization
- Use OnPush change detection strategy
- Implement lazy loading for feature modules
- Use track by functions in *ngFor loops
- Preload critical routes
- Optimize bundle size with tree shaking

### 2. State Management
- Use signals for local component state
- Consider NgRx for complex global state
- Keep services as the single source of truth
- Use computed signals for derived state

### 3. Error Handling
- Implement global error handler
- Show user-friendly error messages
- Log errors to external service
- Provide fallback UI states

### 4. Accessibility
- Use semantic HTML elements
- Add ARIA labels where needed
- Ensure keyboard navigation works
- Test with screen readers
- Maintain color contrast ratios

### 5. Security
- Sanitize user input
- Use Angular's built-in XSS protection
- Implement CSP headers
- Store tokens securely
- Validate all API responses

## Next Steps

1. **Complete remaining components**: Story detail, edit, and list views
2. **Add advanced features**: Real-time updates, collaborative editing
3. **Implement PWA features**: Offline support, push notifications
4. **Add animations**: Page transitions, micro-interactions
5. **Optimize for mobile**: Touch gestures, responsive design
6. **Add i18n support**: Multiple languages
7. **Implement analytics**: User behavior tracking
8. **Add social features**: Sharing, comments, likes

This completes the Phase 2 Angular implementation guide. The frontend is now ready to provide a rich, interactive experience for the GenStoryAI platform.