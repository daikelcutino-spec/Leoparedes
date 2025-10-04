# Highrise Bot Application

## Overview

This is a Highrise bot application built with Python that manages automated interactions, user moderation, and special features within a Highrise virtual room. The bot handles user permissions (VIP, moderators, admins), automated emote cycles, spatial zone management, user activity tracking, and economy features including a heart-based currency system.

## Recent Changes

**October 4, 2025 - Session 3**
- ✅ **Fixed Auto Emote Cycle Startup**: Resolved issue where 224-emote cycle wasn't starting
  - Simplified on_start method by removing blocking chat messages
  - Enhanced start_auto_emote_cycle with cycle counter and progress logging (every 20 emotes)
  - Added bot_mode check to allow stopping cycle if needed
  - Added better error handling and recovery
- ✅ **Improved Flashmode Auto-teleport**: Enhanced on_user_move for better reliability
  - Clarified logic: only activates for floor changes (Y >= 1.0) with minimal horizontal movement
  - Added explicit axis delta calculations for better precision
  - Improved cooldown messaging and logging
  - Added comprehensive documentation in code
- ✅ Verified all features working correctly with no errors

**October 4, 2025 - Session 2**
- ✅ **Enhanced Reaction Commands**: Modified !thumbs, !clap, !wave to support advanced features
- ✅ **Multiple Reactions**: Commands now support !thumbs/@clap/@wave @user [cantidad] to send multiple reactions (up to 30)
- ✅ **Broadcast Reactions**: Commands now support !thumbs/@clap/@wave all to send reactions to all users in room
- ✅ **Pattern Consistency**: All reaction commands now follow the same pattern as !heart command
- ✅ Verified !inventory command already present and working (ADMIN/OWNER only)
- ✅ Bot tested and running successfully without errors

**October 4, 2025 - Session 1**
- ✅ **MASSIVE FEATURE UPDATE**: Added 8 new command systems with 30+ new commands
- ✅ **Sistema de Inventario**: !inventory @user, !give @user [item_id] (ADMIN/OWNER only)
- ✅ **Moderación Extendida**: !unmute, !unban, !banlist, !mutelist, modified !mute to use seconds
- ✅ **Sistema de Movimiento (Walk)**: !walk [x] [y] [z], !walkto @user - bot walks gradually instead of teleporting
- ✅ **Sistema de Anchors**: !anchor [id] @user, !setanchor [id], !listanchors (ADMIN/OWNER)
- ✅ **Sistema de Privilegios**: !setmod @user, !removemod @user, !privilege @user (ADMIN/OWNER)
- ✅ **Sistema de Canales**: !channel create/invite/kick/delete (with API limitation notes)
- ✅ **Sistema de Voice/Audio**: !voice enable/disable/mute/unmute (with API limitation notes)
- ✅ **Sistema de Room Settings**: !roomset private/public/capacity/name/description (with API limitation notes)
- ✅ **Nuevas Reacciones**: !thumbs @user, !clap @user, !wave @user (available to all users)
- ✅ **Modified !tome**: Bot now walks gradually to owner instead of instant teleport
- ✅ **Modified !bot @user**: Bot walks to user, performs action, walks back to original position
- ✅ Added ANCHOR_POINTS global dictionary for anchor system
- ✅ All new commands tested and working correctly

**October 3, 2025**
- ✅ **MAJOR REFACTORING**: Unified command handling system for public chat and whisper commands
- ✅ Created central `handle_command` method that processes all commands with automatic response routing
- ✅ Commands now work seamlessly in both public chat (with @ mention) and private whispers
- ✅ Refactored `on_chat` method (reduced from 2000+ lines to 56 lines)
- ✅ Added new `on_whisper` method to handle private whisper commands
- ✅ Removed 690 lines of duplicate code (file reduced from 6397 to 5708 lines)
- ✅ All commands now use unified `send_response()` helper for smart routing
- ✅ Bot tested and running successfully with no errors

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

**Problem**: Users need to interact with bot features through both public chat and private whispers.

**Solution**: Unified command handling system with three-layer architecture:

1. **`handle_command` method** (Line 733): Central command processor that:
   - Accepts `is_whisper` parameter to determine response routing
   - Uses internal `send_response()` helper function
   - Routes responses to whisper (private) or public chat based on context
   - Contains all command logic in one place (~4000 lines)

2. **`on_chat` method** (Line 4810): Handles public chat messages:
   - Performs initialization (user tracking, ban/mute checks, bot mention detection)
   - Calls `handle_command(user, msg, is_whisper=False)` for commands
   - Sends public responses with @ mention

3. **`on_whisper` method** (Line 4866): Handles private whisper messages:
   - Performs initialization (user tracking, ban/mute checks)
   - Calls `handle_command(user, msg, is_whisper=True)` for commands
   - Sends responses via private whisper

**Key Features**:
- Commands work identically in both public chat and whispers
- Role-based access control enforced in `handle_command`
- Smart response routing via `send_response()` helper
- Supports all command types: user commands (!hearts, !emote), moderation (!ban, !mute, !kick), admin (!vip, !zone)

**Design Pattern**: Centralized command pattern with context-aware response routing and role-based access checks.

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