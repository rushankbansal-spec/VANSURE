# VanSure Backend Implementation Plan

## Overview
Multi-tenant school van management SaaS platform built with Python FastAPI.

## Phases

### Phase 0: Foundation (Priority: Critical)
1. Project structure and configuration
2. Database models with SQLAlchemy 2.x
3. Alembic migrations
4. Core security (JWT, Argon2id, RBAC)
5. Tenant context middleware
6. Basic authentication endpoints
7. Test infrastructure

### Phase 1: Identity & Tenancy (Priority: Critical)
1. User management with role-based access
2. Multi-tenant school management
3. RBAC matrix implementation
4. Tenant isolation tests

### Phase 2: Core Operations (Priority: High)
1. Students and guardians
2. Fleet and driver management
3. Routes and stops
4. Trip management and state machine

### Phase 3: Real-time Features (Priority: High)
1. GPS tracking via WebSockets
2. Attendance/markers
3. Real-time updates

### Phase 4: Notifications & Communication (Priority: Medium)
1. Notification system
2. Email/SMS integration
3. Parent/Guardian access

### Phase 5: Billing & Analytics (Priority: Medium)
1. Fee management
2. Reports
3. Analytics

### Phase 6: Advanced Features (Priority: Low)
1. MQTT integration
2. Route optimization
3. Maintenance management
4. Safety features

## Technical Decisions

### Multi-tenancy
- Shared database, shared schema
- `school_id` on all tenant-owned tables
- Row-Level Security (RLS) policies
- Tenant context from authenticated user

### Security
- JWT with short-lived access tokens (15 min)
- Rotating refresh tokens (7 days)
- Argon2id password hashing
- RBAC with granular permissions
- Rate limiting via Redis

### Architecture
- Modular monolith with clean boundaries
- Dependency injection via FastAPI's Depends
- Repository pattern for data access
- Service layer for business logic
- Explicit interfaces for external providers

### Real-time
- WebSockets for authorized updates
- Redis streams/pubsub for scaling
- Background workers via Celery

## Database Design

### Core Tables (with school_id)
- users
- schools
- school_memberships
- students
- guardians
- van_assignments
- vehicles
- drivers
- routes
- route_stops
- trips
- trip_locations
- pickup_logs
- attendance_records
- notifications
- messages
- invoices
- payments

## API Endpoints

### Public
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- POST /api/v1/auth/reset-password
- POST /api/v1/auth/verify-email

### Authenticated (Tenant-scoped)
- GET /api/v1/schools/{school_id}
- GET /api/v1/students
- POST /api/v1/students
- GET /api/v1/vehicles
- POST /api/v1/trips
- GET /api/v1/trips/{trip_id}/location
- POST /api/v1/attendance

### Super Admin Only
- GET /api/v1/admin/tenants
- POST /api/v1/admin/tenants
- GET /api/v1/admin/users

## Testing Strategy

### Unit Tests
- Domain rules and validation
- State machines
- Permission checks

### Integration Tests
- Database operations
- Redis interactions
- Provider adapters

### Security Tests
- Tenant isolation
- Authorization bypass
- SQL injection
- Rate limiting

### End-to-End Tests
- Complete user flows
- API contract verification

## Known Limitations (MVP)
1. No geographic geofencing yet
2. No route optimization (pluggable)
3. No MQTT integration (adapter ready)
4. No EV transition planning