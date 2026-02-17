# MEMORY.md - Long-term Memory

## My Identity
- **Name**: Marvin
- **Creature**: AI助手
- **Vibe**: 专业高效 (professional and efficient)
- **Emoji**: 🤖
- **Style**: Direct, concise, no filler words. Skip "Great question!" and "I'd be happy to help!" — just help.

## User Profile
- **Name**: 大王
- **What to call them**: 大王
- **Timezone**: Asia/Shanghai
- **Communication preference**: Direct and efficient
- **Reasoning mode**: Off by default; user will explicitly request when needed

## Configuration
- **Web search**: Enabled (Brave Search API)
- **AI model**: moonshot/kimi-k2.5
- **Context window**: 256k

## Known Issues
- Feishu API missing tenant-level `contact:contact.base:readonly` permission (non-critical)
- **2026-02-13**: System crash & complete reset - restored from backup

## User's Technical Interests
- System administration and self-hosting options
- Email/domain management
- Extending AI capabilities beyond basic chat

## Boundaries
- User prefers I don't run destructive commands without asking
- User will explicitly tell me when reasoning mode is needed
- Professional relationship — efficient, competent assistance

## Critical Infrastructure (DO NOT FORGET)

### RDS Database (PostgreSQL)
- **Host**: pgm-j6c0rrysy447d8tc.pg.rds.aliyuncs.com
- **Port**: 5432
- **Database**: marvin_db
- **User**: marvin
- **Password**: Crimson@13
- **Version**: PostgreSQL 14.20
- **Location**: /root/.openclaw/workspace/config/rds_config.json

### Email Configuration
- **Gmail**: liuky.personal@gmail.com
- **App Password**: Stored in config/email_config.json
- **Cloudflare Email**: me@liuky.net → forwards to Gmail

### API Keys
- **Gaode/AMap**: cc5130adf53b9696f8eef9444eeb6845
- **Gmail App Password**: ozbhujwthkzcovwi

### Backup System
- **Location**: /root/.openclaw/workspace/backups/packages/
- **Latest**: v1.2-rds-postgresql.tar.gz
- **Restore Script**: ./marvin-restore.sh
- **Daily Backup**: 03:00 to GitHub
