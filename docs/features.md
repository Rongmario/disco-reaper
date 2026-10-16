# Extensive Feature list
Here's complete list of everything the tool can handle and any specific caveats or workarounds.

- 🟩Fully supported
- 🟧Work Around implemented
- 🟥Limitation

---

# Migration Tool

## Server Identity
* 🟩 **Server Name**
* 🟩 **Server Icon**
* 🟩 **Server Banner**

## Server Structure
* 🟩 **Categories**
    - 🟩 **Metadata**: Copies Category names, also preserve the position of the Categories and its child channels.
    - 🟩 **Permission Overwrites**: Copies role-specific permission overwrites set at the category level.
* 🟩 **Channels**
    - 🟩 **Metadata**: Copies Channel names, topics/descriptions.
    - 🟩 **NSFW Flag** is preserved for age restricted channels.
    - 🟧 **Slowmode** timing rules are preserved for text channels (Stoat doesnt have slowmode).
    - 🟩 **Bitrate** setting is also preserved Voice channels
    - 🟩 **Permission Overwrites**: Copies role-specific permission overwrites set on individual channels.

## Roles
*  🟩 **Role Cloning**: Clones every custom role with its original name, color (hex code), and hierarchical position.
*  🟩 **Role Settings**: Copies the "Display role members separately from online members" (hoist) and "Allow anyone to @mention this role" settings.

### Text Messages
* 🟩 **Markdown Support**: Preserves all standard and advanced Discord markdown:
    - `**Bold**`, `*Italics*`, `__Underline__`, `~~Strikethrough~~`.
    - `> Blockquotes` and `>>> Multi-line quotes`.
    - `Code blocks` and ` ```Full code blocks with syntax highlighting``` `.
    - `||Spoilers||`.
* 🟩 **Message Authors**: Preserves the original author's name and avatar in migrated messages.
* 🟩 **Reply Links**: Preserves the connection of replies if the referenced message was previously migrated.
* 🟩 **Embeds**: Clones rich embeds sent by bots or webhooks, including their colors, fields, and descriptions.

### File Attachments
* 🟩 **Media**: Downloads and re-uploads images, videos, and audio clips.
* 🟩 **Documents**: Preserves PDFs, text files, and other message attachments.
* 🟧 **Size Limits**: Automatically checks size limits. If an attachment is too large for the target platform.
> Stoat doesnt support many file types, so those attachments are skipped and an error message will be sent in place of the attachment

### Emojis
* 🟩 **Standard Emojis**: Full support for Unicode emojis.
* 🟩 **Custom Server Emojis**: Automatically clones custom server emojis (both static and animated) to the target server.
* 🟩 **Emoji Mapping in messages**: References to custom emojis in migrated messages are updated to point to the new emoji IDs on the target platform.
* 🟥 **External Emojis**: Emojis from external servers are not migrated; only the `:emoji_name:` will be displayed.

### Stickers
* 🟧 **Normal Stickers**: Migrates static and animated stickers (`.png`, `.apng`, `.gif`).
* 🟧 **Lottie Stickers**: Converted during migration:
    - **Fluxer**: Converted to `.webp` for compatibility.
    - **Stoat**: Converted to `.gif`.
> Stickers are currently migrated as attachments since sending stickers via api is not yet fully supported on target platforms.

### Mentions & Discord Links
* 🟩 **Channel Mentions**: Automatically resolves `#channel` mentions to point to the correct migrated channel on the target server.
* 🟩 **Role Mentions**: Automatically resolves `@role` mentions to point to the cloned role on the target platform.
* 🟩 **User Mentions**: Mentions of users are preserved as text [`@nickname`] if that user.
* 🟩 **Message Links**: Standard Discord message URLs are resolved to the new URL on Fluxer or Stoat (as long as the target message has been migrated).
* 🟩 **Channel Links**: Discord channel URLs (like `discord.com/channels/...`) are resolved to their matching target channel link.

### Threads & Forums
* 🟩 **Active & Archived Threads**: Scans and migrates messages from all threads.
* 🟩 **Fluxer: Native Threads**: Threads are recreated as real threads under their parent channel, keeping the original authors. Archived and locked threads are archived/locked again once their messages are migrated.
* 🟧 **Fluxer: Forum Posts**: Forum posts are created as real posts with their first message during message migration (not while cloning the structure). Forum tags are not copied yet.
* 🟧 **Stoat: Thread Structure**: Stoat has no threads, so thread messages are migrated into their parent channel between thread markers.

### Misc features
* 🟩 **Incremental Sync**: Scans migration database to find the "Last Message ID." It skips duplicate data and continues where it left off.
* 🟩 **Audit Logging**: Creates a `#reaper-logs` channel in the target community and sends status updates and error reports.

---

# Backup Tool
You can create a local snapshot of your Discord server using the Backup Tool. 

* 🟩 **SQLite Database**: All server mappings, message IDs, and content are stored in a SQLite database.
* 🟩 **Deduplicated Attachments**: All the attachment media is stored in a content-addressable storage system.
* 🟩 **Incremental Syncing**: Scans your existing local files and only downloads messages that have been sent since your last backup.
* 🟩 **Supported Migrated**: Local backup can be used to later migrate your data without any dependance on discord API - even if that server was deleted.
## Backup Filters
Set under `backup_filters` in `reaper_config.yaml` (inside your `ReaperFiles-<name>` folder). Edit the file while the tool is closed. The backup confirm screen lists the active filters.

```yaml
backup_filters:
  after_date: 2020-01-01        # skip everything before this day (UTC); threads with no newer messages are skipped too
  exclude_users: [123456789012345678]
  exclude_bots: true            # bots and webhooks
  allow_bots: [432610292342587392]  # bot or webhook IDs kept anyway
  exclude_patterns:             # Python regex, tested against message content
    - '(?i)^!roll\b'
  media_mode: links             # download (default) or links
```

* 🟧 **Filters apply at backup time**: Filtered messages are never saved. Changing a filter only affects messages backed up afterwards, so start a fresh backup to apply it to older messages.
* 🟧 **Replies**: A reply to a filtered message is kept, but loses its reply link.

## Media Review
* 🟩 **Media manifest**: Every backup run writes `media_manifest.csv` next to `backup.db`, one row per attachment with its message link, channel, author, local file and CDN link.
* 🟩 **Exclude list**: Put attachment IDs or file hashes in `media_exclude.txt` next to `backup.db`, one per line (`#` starts a comment). A path like `attachments/<hash>.png` also works. Excluded files are not downloaded and not migrated.
* 🟩 **Links mode**: With `media_mode: links`, attachments are recorded but not downloaded. Review them with the manifest, add the unwanted ones to `media_exclude.txt`, then set `media_mode: download` and run **Update Existing Backup** to download the rest. Discord CDN links expire after about a day, so the tool re-signs them before downloading.
* 🟥 **Links mode needs Discord**: Attachments still recorded as links have no file, so they are left out of a migration from backup.
