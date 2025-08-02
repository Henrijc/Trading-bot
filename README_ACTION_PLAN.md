# AI Crypto Trading Coach - Action Plan for Next Agent

## Current Application State

The AI Crypto Trading Coach is a full-stack application with React frontend, FastAPI backend, and MongoDB database. The application has recently undergone a major architectural shift to a release-based deployment model using GitHub Container Registry (GHCR) to resolve persistent build and runtime issues.

### Architecture Overview
```
Frontend (React) ↔ Backend (FastAPI) ↔ MongoDB
                ↕
        Trading Bot (Freqtrade-inspired)
```

### Recent Major Changes
- Deployment strategy moved to GitHub Container Registry (GHCR)
- CI/CD pipeline refactored into build-and-push and deploy-to-server jobs
- Dockerfiles optimized for reliable builds
- SSH timeouts increased to prevent deployment failures
- **JUST COMPLETED**: GitHub workflow SSH secrets updated to use `_C_BOT_` naming convention:
  - `VPS_HOST` → `VPS_C_BOT_HOST`
  - `VPS_USER` → `VPS_C_BOT_USER` 
  - `VPS_SSH_KEY` → `VPS_SSH_C_BOT_KEY`

## Current Status & Completed Tasks

### ✅ Recently Completed
- **GitHub Workflow SSH Configuration**: Updated `.github/workflows/deploy.yml` to use new secret naming convention:
  ```yaml
  host: ${{ secrets.VPS_C_BOT_HOST }}
  username: ${{ secrets.VPS_C_BOT_USER }}
  key: ${{ secrets.VPS_SSH_C_BOT_KEY }}
  ```
- **Deployment Architecture**: Moved to GHCR-based deployment model
- **Docker Optimization**: All Dockerfiles refined for reliable builds

### ⏳ Next Required Action
**CRITICAL**: Ensure GitHub repository secrets are configured with the new names before deployment.

## Pending Tasks (Priority Order)

### Phase 1: UI Fixes & Improvements
1. **Fix amber/gold colors on login page (`LoginSystem.jsx`)**
   - Issue: Colors don't match the black/cyan theme
   - Location: `/app/frontend/src/components/LoginSystem.jsx`
   - Expected: Consistent black/cyan color scheme

2. **Resolve 2-hour timestamp discrepancy for AI messages**
   - Issue: AI messages show incorrect timestamps (2 hours off)
   - Affects: Chat interface and message display
   - Expected: Accurate local timezone timestamps

### Phase 2: API Optimization & Integration
3. **Diagnose and optimize Google Gemini API problems**
   - Issue: Timeouts and non-responsiveness
   - Impact: AI responses failing
   - Action: Debug API calls, optimize error handling

4. **Implement TikTok integration for social sentiment analysis**
   - Purpose: Analyze social sentiment for trading insights
   - Requirements: TikTok API credentials needed
   - Integration: New service for sentiment analysis

### Phase 3: System Refinement
5. **Refine crypto_coach_installer_v2.sh script**
   - Goal: Make installation more comprehensive
   - Location: `/app/crypto_coach_installer_v2.sh`
   - Improvements: Better error handling, dependency checks

## Critical Instructions for Next Agent

### 1. MANDATORY First Steps
- **ALWAYS read `/app/test_result.md` first** - contains testing protocols and previous agent communications
- Use `ask_human` tool to confirm any plan before starting
- Read the original user problem statement in `/app/test_result.md`

### 2. Environment & URL Rules (CRITICAL)
```bash
# Protected environment variables - DO NOT MODIFY
REACT_APP_BACKEND_URL  # Frontend .env
MONGO_URL              # Backend .env
```

- Frontend must use `REACT_APP_BACKEND_URL` for all API calls
- Backend must use `MONGO_URL` for database connections
- All backend API routes MUST have `/api` prefix for Kubernetes routing
- Never hardcode URLs or ports

### 3. Testing Protocol
- **Backend testing first**: Use `deep_testing_backend_v2` 
- **Frontend testing**: Only after user approval via `ask_human`
- **Read `test_result.md`** before invoking any testing agent
- Never invoke `deep_testing_frontend_v2` without explicit user permission

### 4. Service Management
```bash
# Service control commands
sudo supervisorctl restart all
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Log checking
tail -n 100 /var/log/supervisor/backend.*.log
```

### 5. Dependency Management
- **Frontend**: Use `yarn` only (never npm)
- **Backend**: Add new packages to `requirements.txt` first
- **Database**: Use UUIDs only (not MongoDB ObjectID)

## Technical Context

### Key Files to Understand
```
/app/
├── backend/server.py              # Main FastAPI app
├── frontend/src/components/       # React components
├── freqtrade/                     # Trading bot
├── vps_deployment_package/        # Production deployment
├── .github/workflows/deploy.yml   # CI/CD pipeline (RECENTLY UPDATED)
└── test_result.md                 # CRITICAL: Testing protocols
```

**Important**: The GitHub workflow has been updated to use new SSH secret names. Ensure these secrets are configured in GitHub:
- `VPS_C_BOT_HOST` - VPS server IP/hostname
- `VPS_C_BOT_USER` - VPS username  
- `VPS_SSH_C_BOT_KEY` - SSH private key

### Color Scheme
- Primary: Black background
- Accent: Cyan (#00FFFF)
- Avoid: Amber, gold, yellow tones

### API Integration Notes
- Google Gemini: Currently experiencing timeouts
- TikTok API: Not yet integrated (credentials needed)
- Luno API: Already integrated for trading

## Implementation Strategy

### Phase 1 Approach
1. Start with login page color fixes (low risk)
2. Test changes using screenshot tool
3. Fix timestamp issues in chat components
4. Verify timezone handling

### Phase 2 Approach
1. Use `integration_playbook_expert_v2` for TikTok integration
2. Debug Gemini API with proper error logging
3. Implement robust error handling for API timeouts
4. Test integrations thoroughly

### Phase 3 Approach
1. Review current installer script
2. Add comprehensive dependency checks
3. Improve error messages and logging

## Emergency Contacts & Escalation

### When to Call Troubleshoot Agent
- After 3 consecutive failed attempts at same operation
- Same error appears twice
- Services won't start or are unresponsive
- User reports "nothing is working"

### When to Call Support Agent
- Questions about platform capabilities
- Git/GitHub related issues
- User complaints or refund requests
- Deployment or Emergent platform questions

## File Structure Context

The application follows a microservices architecture with:
- **Frontend**: React with Tailwind CSS
- **Backend**: FastAPI with MongoDB
- **Trading Bot**: Freqtrade-inspired with FreqAI
- **Deployment**: Docker Compose with GHCR images

## Final Notes

1. **Always prioritize user experience** - fix visible issues first
2. **Test incrementally** - don't make large changes without testing
3. **Document API keys needed** - ask user for credentials upfront
4. **Follow the color scheme** - black/cyan theme is critical
5. **Use environment variables** - never hardcode configurations

Remember: This is an MVP focused on R100,000 monthly profit goal. Focus on core functionality over extensive documentation or over-engineering.