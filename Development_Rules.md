# Development Rules for AI Crypto Trading Coach

## Overview
This document outlines critical development rules that MUST be followed by any engineer working on this AI Crypto Trading Coach application after session forking or new development cycles.

## Critical Development Rules

### 1. NO EMOTICONS OR EMOJIS
- Strictly prohibited in all code, comments, documentation, UI text, and communications
- Maintain professional, clinical appearance throughout the application

### 2. DO NOT BREAK EXISTING CODE
- Never modify working functionality without explicit user approval
- Always test changes thoroughly before confirming fixes
- Maintain backward compatibility unless specifically requested otherwise
- Review all dependencies and imports when making changes

### 3. CONSULT USER FIRST WHEN ENCOUNTERING OBSTACLES
- ALWAYS ask the user before attempting to fix any unexpected issues
- Do not make assumptions about solutions
- Present options and get approval before proceeding
- Use ask_human tool when uncertain about approach

### 4. USE BEST CODING APPROACHES AND ARCHITECTURE REUSE
- Follow existing code patterns and architecture
- Reuse working components and services
- Maintain consistent code style throughout the application
- Leverage established patterns for new features

### 5. ACKNOWLEDGE RULES BEFORE STARTING
- Every new engineer MUST confirm acknowledgment of these rules before editing any code
- Read and understand the complete codebase structure before making changes
- Review test_result.md for current status and implementation history

### 6. NEVER CONFIRM FIXES WITHOUT TESTING
- All changes must be tested using the appropriate testing agents
- Backend changes require deep_testing_backend_v2 verification
- Frontend changes require user approval before testing
- Update test_result.md with proper testing results

## Technical Guidelines

### URL and Environment Management
- NEVER modify URLs or ports in .env files
- Use environment variables exclusively (REACT_APP_BACKEND_URL, MONGO_URL)
- All backend routes must use '/api' prefix
- Internal service ports are correctly configured - do not change

### Testing Protocol
- ALWAYS read test_result.md before invoking testing agents
- Follow the exact testing protocol outlined in test_result.md
- Test backend first, then ask user permission for frontend testing
- Never fix issues already resolved by testing agents

### Service Management
- Use supervisor for service control (restart frontend/backend/all)
- Check supervisor logs for startup issues
- Add new dependencies to requirements.txt and package.json
- Use yarn (not npm) for frontend dependencies

## Current Application Status

### Working Features (DO NOT BREAK)
- Google 2FA Authentication System
- Real-time Luno API Integration
- AI Conversational Interface with Gemini
- Technical Analysis Service
- Freqtrade-Inspired Backtesting System
- Dynamic Target Management
- Session Management and Memory
- UTC Timestamp Consistency
- Portfolio Analysis and Risk Management

### Known Architecture
- Frontend: React with Tailwind CSS and Shadcn/ui components
- Backend: FastAPI with MongoDB database
- AI Service: Google Gemini via litellm
- External APIs: Luno, CoinGecko, CCXT for exchanges

### Color Scheme
- Current: Amber/gold theme (main dashboard)
- Target: Black/turquoise theme (partially implemented in backtesting)
- Inconsistency exists and needs resolution

## Session Handover Requirements

When taking over from another engineer:
1. Read this Development_Rules.md file completely
2. Confirm acknowledgment of all rules
3. Review test_result.md for current implementation status
4. Understand pending_tasks and current_work from system context
5. Get user approval before making any changes

## Emergency Protocols

### If Services Fail
1. Check supervisor logs: `tail -n 100 /var/log/supervisor/backend.*.log`
2. Verify environment variables in .env files
3. Check for missing dependencies in requirements.txt
4. Call troubleshoot_agent after 3 failed attempts

### If Testing Fails
1. Update test_result.md with failure details
2. Use testing agents according to protocol
3. Never mock responses without user permission
4. Ask user before attempting minor fixes

## Compliance Verification

By working on this application, you confirm:
- [ ] I have read and understand all development rules
- [ ] I will not use emoticons or emojis anywhere
- [ ] I will not break existing working code
- [ ] I will consult the user before fixing obstacles
- [ ] I will use established coding approaches
- [ ] I will test all changes before confirming fixes
- [ ] I acknowledge these rules before starting any edits

**Date Created:** June 2025  
**Version:** 1.0  
**Last Updated:** Current Session