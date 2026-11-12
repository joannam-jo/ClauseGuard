import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Moon, Sun, FileText, LayoutDashboard, Upload, Menu, Brain, LogIn, LogOut, User } from 'lucide-react';
import { Button } from './components/ui/button';
import { Toaster } from './components/ui/sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from './components/ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger } from './components/ui/sheet';
import { Avatar, AvatarFallback, AvatarImage } from './components/ui/avatar';

// Pages
import Home from './pages/Home';
import UploadPage from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';
import Dashboard from './pages/Dashboard';
import MLDashboard from './pages/MLDashboard';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Store
import { useThemeStore, useAuthStore } from './store/analysisStore';
import { authApi } from './services/api';
import { toast } from 'sonner';

import './App.css';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const NAV_LINKS = [
  { to: '/', label: 'Home', icon: FileText },
  { to: '/upload', label: 'Upload', icon: Upload },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/ml', label: 'ML Models', icon: Brain },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore();
  return (
    <Button variant="ghost" size="icon" onClick={toggleTheme} data-testid="theme-toggle">
      {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
    </Button>
  );
}

function NavLinkItem({ to, label, icon: Icon, currentPath }) {
  return (
    <Link to={to}>
      <Button variant={currentPath === to ? 'secondary' : 'ghost'} size="sm">
        <Icon className="w-4 h-4 mr-2" />
        {label}
      </Button>
    </Link>
  );
}

function UserMenu({ user, onLogout }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="rounded-full" data-testid="user-menu-trigger">
          <Avatar className="w-8 h-8">
            <AvatarImage src={user.picture} alt={user.name} />
            <AvatarFallback>{user.name?.charAt(0) ?? 'U'}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <div className="px-2 py-1.5">
          <p className="text-sm font-medium">{user.name}</p>
          <p className="text-xs text-muted-foreground">{user.email}</p>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onLogout} data-testid="logout-menu-item">
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function MobileNavDrawer({ navLinks, isAuthenticated, currentPath }) {
  return (
    <Sheet>
      <SheetTrigger asChild className="md:hidden">
        <Button variant="ghost" size="icon">
          <Menu className="w-5 h-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-64">
        <nav className="flex flex-col gap-2 mt-8">
          {navLinks.map((link) => (
            <Link key={link.to} to={link.to}>
              <Button
                variant={currentPath === link.to ? 'secondary' : 'ghost'}
                className="w-full justify-start"
              >
                <link.icon className="w-4 h-4 mr-2" />
                {link.label}
              </Button>
            </Link>
          ))}
          {!isAuthenticated && (
            <>
              <Link to="/login">
                <Button variant="outline" className="w-full justify-start">
                  <LogIn className="w-4 h-4 mr-2" />
                  Login
                </Button>
              </Link>
              <Link to="/register">
                <Button className="w-full justify-start">
                  <User className="w-4 h-4 mr-2" />
                  Sign Up
                </Button>
              </Link>
            </>
          )}
        </nav>
      </SheetContent>
    </Sheet>
  );
}

function ProtectedRoute({ children }) {
  const location = useLocation();
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();

  // Hide nav on analysis page (it has its own header)
  if (location.pathname.startsWith('/analysis/')) return null;

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      console.warn('Logout request failed:', e.message);
    }
    logout();
    toast.success('Logged out successfully');
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-50 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <FileText className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-semibold hidden sm:inline">Finance Analyzer</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => (
              <NavLinkItem
                key={link.to}
                to={link.to}
                label={link.label}
                icon={link.icon}
                currentPath={location.pathname}
              />
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {isAuthenticated && user ? (
              <UserMenu user={user} onLogout={handleLogout} />
            ) : (
              <Link to="/login">
                <Button variant="outline" size="sm" data-testid="login-nav-button">
                  <LogIn className="w-4 h-4 mr-2" />
                  Login
                </Button>
              </Link>
            )}
            <MobileNavDrawer
              navLinks={NAV_LINKS}
              isAuthenticated={isAuthenticated}
              currentPath={location.pathname}
            />
          </div>
        </div>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

function AppContent() {
  return (
    <>
      <Navigation />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route
            path="/analysis/:documentId"
            element={
              <ProtectedRoute>
                <AnalysisPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/ml" element={<MLDashboard />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </main>
      <Toaster position="bottom-right" />
    </>
  );
}

export default function App() {
  const { setTheme } = useThemeStore();
  const { isAuthenticated, setUser, clearUser } = useAuthStore();

  // Initialize theme on mount
  useEffect(() => {
    const stored = localStorage.getItem('theme-store');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.state?.theme) {
          document.documentElement.classList.toggle('dark', parsed.state.theme === 'dark');
          return;
        }
      } catch (e) {
        console.warn('Invalid theme data in localStorage:', e.message);
      }
    }
    document.documentElement.classList.remove('dark');
    setTheme('light');
  }, [setTheme]);

  // Verify session with server on mount (validates httpOnly cookie)
  useEffect(() => {
    const verifySession = async () => {
      if (isAuthenticated) {
        try {
          const response = await authApi.me();
          setUser(response.data);
        } catch (e) {
          clearUser();
        }
      }
    };
    verifySession();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for 401 unauthorized events dispatched by the API interceptor
  useEffect(() => {
    const handleUnauthorized = () => clearUser();
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [clearUser]);

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-background">
        <AppContent />
      </div>
    </BrowserRouter>
  );
}
