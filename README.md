# GitHub Commit Statistics Generator 📊

> A streamlined fork of [anmol098/waka-readme-stats](https://github.com/anmol098/waka-readme-stats) focused on commit analytics.

<p align="center">
   <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/language-python-blue?style" alt="Python Badge"/>
   </a>
   <a href="https://github.com/VatsalSy/commits-readme-stats/blob/main/LICENSE">
      <img src="https://img.shields.io/github/license/VatsalSy/commits-readme-stats" alt="License Badge"/>
   </a>
   <a href="https://github.com/VatsalSy/commits-readme-stats/stargazers">
      <img src="https://img.shields.io/github/stars/VatsalSy/commits-readme-stats" alt="Stars Badge"/>
   </a>
   <a href="https://github.com/VatsalSy/commits-readme-stats/network/members">
      <img src="https://img.shields.io/github/forks/VatsalSy/commits-readme-stats" alt="Forks Badge"/>
   </a>
   <a href="https://github.com/VatsalSy/commits-readme-stats">
      <img src="https://img.shields.io/static/v1?label=%F0%9F%8C%9F&message=If%20Useful&style=style=flat&color=BC4E99" alt="Star Badge"/>
   </a>
   <a href="https://github.com/VatsalSy/commits-readme-stats/actions/workflows/security-audit.yml">
      <img src="https://github.com/VatsalSy/commits-readme-stats/actions/workflows/security-audit.yml/badge.svg" alt="Security Audit"/>
   </a>
   <a href="https://github.com/VatsalSy/commits-readme-stats/releases">
      <img src="https://img.shields.io/github/v/release/VatsalSy/commits-readme-stats?include_prereleases" alt="GitHub release"/>
   </a>
</p>

<p align="center">
   Are you an early 🐤 or a night 🦉?
   <br/>
   When are you most productive during the day?
   <br/>
   Let's analyze your commit patterns!
</p>

## Key Features

🎯 **Focused Implementation**
- Specializes in commit analytics with optional WakaTime integration
- Tracks commit timing patterns and most productive days
- Perfect for understanding your coding schedule

🔄 **Smart Commit Tracking**
- Prevents double-counting of commits across branches
- Uses commit hash tracking for accurate statistics
- Handles merge commits and branch synchronization intelligently

📊 **Analytics Include**
- Time of day commit patterns (Early Bird vs Night Owl)
- Most productive days of the week
- Clean, visual representation of commit habits

⏱️ **WakaTime Integration** (Optional)
- Programming languages breakdown
- Editors/IDEs usage
- Projects time distribution
- Operating system stats

## Comparison with Original

| Feature | commits-readme-stats | waka-readme-stats |
|---------|---------------------|-------------------|
| Commit Time Analytics | ✅ | ✅ |
| WakaTime Integration | ✅ (opt-in) | ✅ (required) |
| Prevent Double Counting | ✅ | ❌ |
| Setup Complexity | Simple | Complex |
| Focus | Commit + WakaTime | Full Coding Stats |

## Local Setup

1. Clone the repository
2. Create a `.env` file:
```env
INPUT_GH_COMMIT_TOKEN=your_github_personal_access_token

# Optional: WakaTime integration
INPUT_WAKATIME_API_KEY=your_wakatime_api_key
INPUT_SHOW_WAKATIME=True
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run locally:
```bash
python github_stats.py <username>
```

## Local Testing

1. Copy `workflow_dispatch.json.example` to `workflow_dispatch.json`
2. Update the values in your local `workflow_dispatch.json` as needed
3. Run the test script:

```bash
bash runTestLocallyDocker.sh
```

## GitHub Action Setup

**Note:** The token names for GitHub Actions are different from the local setup.

1. Create `.github/workflows/github-stats.yml`:
```yaml
name: GitHub Stats Update
on:
  schedule:
    - cron: '0 */4 * * *'  # Runs every 4 hours
  workflow_dispatch:      # Allows manual trigger

jobs:
  update-stats:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GH_COMMIT_TOKEN }}

      - name: Generate Stats
        uses: VatsalSy/commits-readme-stats@v3.0
        with:
          GH_COMMIT_TOKEN: ${{ secrets.GH_COMMIT_TOKEN }}
          SHOW_COMMIT: true
          SHOW_DAYS_OF_WEEK: true
          # WakaTime (optional - uncomment to enable)
          # WAKATIME_API_KEY: ${{ secrets.WAKATIME_API_KEY }}
          # SHOW_WAKATIME: true
          COMMIT_MESSAGE: 'docs(stats): update github stats'
          COMMIT_BY_ME: false
          COMMIT_USERNAME: 'github-actions[bot]'
          COMMIT_EMAIL: '41898282+github-actions[bot]@users.noreply.github.com'

```

2. Add these markers to your README.md:
```markdown
<!--START_SECTION:github-stats-->
<!--END_SECTION:github-stats-->
```

3. (Optional) For WakaTime stats, add this separate section:
```markdown
<!--START_SECTION:wakatime-->
<!--END_SECTION:wakatime-->
```

4. Set up GitHub Personal Access Token:
   - Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
   - Generate a token with `repo` and `user` scopes
   - Add the token as a repository secret named `GH_COMMIT_TOKEN`

## Configuration Options

### Core Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `GH_COMMIT_TOKEN` | GitHub Personal Access Token | Yes | N/A |
| `SHOW_COMMIT` | Show commit timing patterns | No | `true` |
| `SHOW_DAYS_OF_WEEK` | Show most productive days | No | `true` |
| `SHOW_TOTAL_COMMITS` | Show total number of commits | No | `true` |
| `COMMIT_MESSAGE` | Custom commit message | No | `'docs(stats): update github stats'` |
| `COMMIT_BY_ME` | Whether commits should be authored by token owner | No | `false` |
| `COMMIT_USERNAME` | Username for commit author | No | `'github-actions[bot]'` |
| `COMMIT_EMAIL` | Email for commit author | No | `'41898282+github-actions[bot]@users.noreply.github.com'` |

### WakaTime Options (Optional)

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `WAKATIME_API_KEY` | WakaTime API key for coding activity stats | No | `''` |
| `SHOW_WAKATIME` | Enable WakaTime stats (requires API key) | No | `false` |
| `SHOW_LANGUAGE` | Show programming languages from WakaTime | No | `true` |
| `SHOW_EDITORS` | Show editors from WakaTime | No | `true` |
| `SHOW_PROJECTS` | Show projects from WakaTime | No | `true` |
| `SHOW_OS` | Show operating systems from WakaTime | No | `true` |

> **Note:** WakaTime integration requires both `WAKATIME_API_KEY` and `SHOW_WAKATIME: true` to be set.
> Get your WakaTime API key from [WakaTime Settings](https://wakatime.com/settings/api-key).

## Authentication and Usage

### GitHub Token Requirements
- The script requires a GitHub Personal Access Token (PAT) to fetch repository statistics
- **Important**: The token owner must match the username being queried. For example:
  - If your token belongs to user `VatsalSy`, the script will work with:
    ```bash
    python github_stats.py VatsalSy --debug
    ```
  - To query stats for a different user (e.g., `temp-user`), you need a token generated by that user's account

### Getting a Token
1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate a new token with the following permissions:
   - `repo` (for repository access)
   - `user` (for user data access)
3. Save the token securely and use it in the script

### Running the Script

```bash
# Use the script with the token owner's username
python github_stats.py USERNAME --debug

# Example:
python github_stats.py VatsalSy --debug
```

## License

MIT License - see [LICENSE](LICENSE) for details.
