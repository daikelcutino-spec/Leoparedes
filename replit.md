# Highrise Bot Application

## Overview

This project is a Python-based Highrise bot application designed to manage automated interactions, user moderation, and special features within a Highrise virtual room. Its primary purpose is to create an engaging and controlled environment by handling user permissions, automating emotes, managing spatial zones, tracking user activity, and implementing a heart-based economy system. The project aims to provide a robust and automated presence that enhances the user experience within the Highrise platform.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Bot Architecture

The bot uses an event-driven architecture built on the Highrise SDK's `BaseBot` class, leveraging async/await patterns for real-time event handling. Key design decisions include:
- Asynchronous event handlers for chat messages, user lifecycle events, and position changes.
- Centralized configuration via `config.json` for room settings and zone definitions.
- Secrets-based credential management using environment variables for sensitive data.
- File-based persistence for user data (hearts, activity, user info, bans, mutes) to simplify deployment.
- A logging system writes operational and interaction data to `bot_log.txt`.

### Authorization & User Management

A role-based access control system with four tiers (Owner, Admins, Moderators, VIP Users) manages hierarchical permissions. User IDs are loaded from `config.json` (no longer dependent on secrets for local deployment). VIP status and banned/muted users are tracked at runtime and persisted to files.

**Recent Changes (Oct 31, 2025):**
- Removed all dependencies on environment variables/secrets for easier local deployment
- Owner and Admin now have unrestricted access to ALL commands without exceptions
- Owner and Admin bypass all zone restrictions including forbidden zones

### Spatial Zone Management

The system implements coordinate-based zone management, including VIP, DJ, Management, Forbidden, and Jail Zones. It uses Euclidean distance calculations to restrict access and automatically teleport unauthorized users from restricted areas.

**Jail Zone System:**
- Jail zone is a special restricted zone that can only be accessed by users who are sent there by Admin/Owner
- Admin/Owner can send users to jail using `!jail @username` command
- Admin/Owner can free users from jail using `!unjail @username` command
- Users in jail are tracked in the `JAIL_USERS` set
- Regular users cannot voluntarily access the jail zone
- Admin and Owner always have unrestricted access to all zones including jail and forbidden zones

### Economy System

A heart-based virtual economy allows users to earn hearts through activity, transfer them, and enables the bot to manage its own wallet. Hearts are tracked in a dictionary and persisted to `data/hearts.txt`.

### Automated Bot Behavior

The bot features an automated emote cycling system that plays predefined emotes to maintain an active visual presence. This cycle can be interrupted by manual commands. Initial outfit and emote sets are configured via `config.json`.

### Activity Tracking

User engagement is monitored through a multi-metric tracking system that records message counts, last activity timestamps, and join times. This data is persisted to `data/activity.txt` and used for automatic rewards.

### Logging & Monitoring

A structured logging system categorizes events (BOT, CHAT, ADMIN, MOD, ERROR, WARNING), includes timestamps, and stores entries in `bot_log.txt`. Critical events are also output to the console.

### Data Persistence Strategy

A hybrid approach uses JSON files for structured data (`user_info.json`) and plain text files for simple key-value data (`hearts.txt`, `activity.txt`), all organized under the `data/` directory. This strategy prioritizes simplicity and ease of deployment over high-concurrency performance.

### Command System

A unified, three-layer command handling system processes user interactions from both public chat and private whispers. The `handle_command` method acts as a central processor, routing responses contextually via a `send_response()` helper function and enforcing role-based access control.

### Cantinero Bot (Bartender)

A separate `cantinero_bot.py` operates as a bartender, performing a continuous floss emote loop, broadcasting automated public messages, sending welcome whispers, and teleporting to a configured spawn point. It shares room and owner IDs with the main bot but uses a separate API token and minimal configuration in `cantinero_config.json`.

## External Dependencies

- **Highrise SDK**: The primary API for interacting with the Highrise platform, providing `BaseBot` and event handlers. Authentication uses API tokens from environment variables.
- **Python Standard Library**: Utilized for asynchronous operations (`asyncio`), data serialization (`json`), timestamp management (`datetime`, `time`), and type hinting (`typing`).
- **File System**: Used for configuration (`config.json`, `cantinero_config.json`), logging (`bot_log.txt`), and data storage (`data/` directory for user info, hearts, activity).
- **Configuration Files**: All credentials (API tokens, Room IDs, user IDs) are loaded from `config.json` and `cantinero_config.json` for easy local deployment.
- **No External Database**: The project intentionally avoids external database dependencies, relying solely on file-based storage.

## Recent Updates

### October 31, 2025
- **Removed secrets dependency**: All configuration now uses `config.json` files for easier local PC deployment
- **Enhanced permissions**: Owner and Admin now have unrestricted access to ALL commands and zones
- **Jail system**: Added `!jail` and `!unjail` commands for sending users to a restricted jail zone
- **Zone restrictions**: Admin/Owner bypass all forbidden zone restrictions
- **Owner ID updated**: Changed to `64dc252537db1cdb8e202d8d`