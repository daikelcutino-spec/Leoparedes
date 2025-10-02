# Highrise Bot Application

## Overview

This is a Highrise bot application built with Python that manages automated interactions, user moderation, and special features within a Highrise virtual room. The bot handles user permissions (VIP, moderators, admins), automated emote cycles, spatial zone management, user activity tracking, and economy features including a heart-based currency system.

## Recent Changes

**October 2, 2025**
- ✅ Installed Python 3.11.13 runtime environment
- ✅ Installed highrise-bot-sdk (v24.1.0) and dependencies via uv package manager
- ✅ Configured "Highrise Bot" workflow for automatic execution
- ✅ Changed bot default mode from "floss" to "idle" to prevent emote errors
- ✅ Disabled auto-start of floss mode (can be manually activated with !floss command)
- ✅ Bot now connects successfully without errors
- ✅ Integrated "fake floss acelerado" - simulates floss dance with progressive acceleration using free emotes
- ✅ Bot now performs welcome floss dance sequence when connecting to room (~12 seconds duration)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Bot Architecture

**Problem**: Need to create an automated presence in a Highrise room that can moderate users, perform automated actions, and respond to commands.

**Solution**: Event-driven architecture using the Highrise SDK's `BaseBot` class with async/await patterns for handling real-time events.

**Key Design Decisions**:
- Async event handlers for chat messages, user joins/leaves, and position changes
- Centralized configuration via `config.json` for room settings, API credentials, and zone definitions
- File-based persistence for user data (hearts, activity, user info, bans, mutes)
- Logging system that writes to `bot_log.txt` for debugging and audit trails

**Alternatives Considered**: A database-driven approach was not chosen to keep deployment simple and avoid external database dependencies.

### Authorization & User Management

**Problem**: Need hierarchical permission system for different user roles.

**Solution**: Role-based access control with four tiers:
- Owner (highest privileges)
- Admins (can ban, mute, manage users)
- Moderators (can kick, mute, basic moderation)
- VIP Users (access to restricted zones)

**Implementation**:
- User IDs stored in `config.json` for admins, moderators, and owner
- VIP status tracked in runtime set `VIP_USERS` and persisted to file
- Banned/muted users stored in dictionaries with expiration timestamps

### Spatial Zone Management

**Problem**: Restrict access to specific areas within the virtual room.

**Solution**: Coordinate-based zone system with multiple zone types:
- VIP Zone (x, y, z coordinates)
- DJ Zone
- Directivo (Management) Zone
- Forbidden Zones (with radius-based detection)

**Rationale**: Uses Euclidean distance calculation to detect when users enter restricted areas and automatically teleports unauthorized users away.

### Economy System

**Problem**: Engage users with a virtual currency system.

**Solution**: Heart-based economy where users:
- Earn hearts through activity (messages, time spent in room)
- Can transfer hearts to other users
- Bot maintains its own wallet for transactions

**Data Persistence**: Hearts tracked in `USER_HEARTS` dictionary and saved to `data/hearts.txt`.

### Automated Bot Behavior

**Problem**: Bot should appear active and engaging even without commands.

**Solution**: Automated emote cycling system that:
- Plays sequential emotes from a predefined list
- Each emote has specific duration timing
- Cycles continuously for visual presence
- Can be interrupted by manual commands

**Configuration**: Initial outfit and emote set via `config.json` (`bot_initial_outfit`, `bot_initial_emote`).

### Activity Tracking

**Problem**: Monitor user engagement and time spent in room.

**Solution**: Multi-metric tracking system:
- Message count per user
- Last activity timestamp
- Join time tracking (`USER_JOIN_TIMES`)
- Automatic rewards based on activity thresholds

**Data Storage**: Activity data persisted to `data/activity.txt` with format `user_id:messages:last_activity`.

### Logging & Monitoring

**Problem**: Need visibility into bot operations and user interactions.

**Solution**: Structured logging system with:
- Event type categorization (BOT, CHAT, ADMIN, MOD, ERROR, WARNING)
- Timestamp-based entries
- File-based storage in `bot_log.txt`
- Console output for critical events only

**Log Categories**: Bot actions, chat messages, moderation actions, errors filtered by severity.

### Data Persistence Strategy

**Problem**: Maintain state across bot restarts.

**Solution**: Hybrid approach using:
- JSON files for structured data (`user_info.json`)
- Plain text files for simple key-value data (`hearts.txt`, `activity.txt`)
- Data directory organization under `data/` folder

**Trade-offs**: 
- Pros: Simple, no external dependencies, easy to debug
- Cons: Not suitable for high-concurrency or large-scale deployments

### Command System

**Problem**: Users need to interact with bot features.

**Solution**: Chat-based command parser triggered by `!` prefix supporting:
- User commands (!hearts, !emote, !list)
- Moderation commands (!ban, !mute, !kick)
- Admin commands (!vip, !announce, !zone)

**Design Pattern**: Command pattern with role-based access checks before execution.

## External Dependencies

### Highrise SDK
- **Purpose**: Primary API for interacting with Highrise platform
- **Integration**: Provides `BaseBot` class, event handlers, and models for User, Position, Items, etc.
- **Authentication**: API token stored in `config.json`

### Python Standard Library
- **asyncio**: Asynchronous event loop management
- **json**: Configuration and data serialization
- **datetime/time**: Timestamp management and scheduling
- **typing**: Type hints for code clarity

### File System
- **Configuration**: `config.json` - Room ID, API credentials, zone coordinates, user permissions
- **Logging**: `bot_log.txt` - Operational logs and event tracking
- **Data Storage**: `data/` directory containing user information, hearts, and activity files

### No External Database
The application intentionally avoids database dependencies, using file-based storage for simplicity and ease of deployment on Replit.