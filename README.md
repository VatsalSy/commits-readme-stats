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
- Specializes in commit analytics only - clean and efficient
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

## Comparison with Original

| Feature | commits-readme-stats | waka-readme-stats |
|---------|---------------------|-------------------|
| Commit Time Analytics | ✅ | ✅ |
| Language Statistics | ❌ | ✅ |
| Prevent Double Counting | ✅ | ❌ |
| WakaTime Integration | ❌ | ✅ |
| Setup Complexity | Simple | Complex |
| Focus | Commit Patterns | Full Coding Stats |

## Local Setup

1. Clone the repository
2. Create a `.env` file:
```env
INPUT_GH_COMMIT=your_github_personal_access_token
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run locally:
```bash
python github_stats.py <username>
```

## GitHub Action Setup

1. Create `.github/workflows/github-stats.yml`:
```yaml
name: GitHub Stats Update
on:
  schedule:
    - cron: '0 0 * * *'  # Runs daily at midnight
  workflow_dispatch:      # Allows manual trigger
    
jobs:
  update-stats:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GH_COMMIT }}
          
      - name: Generate Stats
        uses: VatsalSy/commits-readme-stats@v2.0.0
        with:
          GH_COMMIT: ${{ secrets.GH_COMMIT }}
          SHOW_COMMIT: true
          SHOW_DAYS_OF_WEEK: true
          COMMIT_MESSAGE: 'docs(stats): update github stats'
```

2. Add these markers to your README.md:
```markdown
<!--START_SECTION:github-stats-->
<!--END_SECTION:github-stats-->
```

3. Set up GitHub Personal Access Token:
   - Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
   - Generate a token with `repo` and `user` scopes
   - Add the token as a repository secret named `GH_COMMIT`

## Configuration Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `GH_COMMIT` | GitHub Personal Access Token | Yes | N/A |
| `SHOW_COMMIT` | Show commit timing patterns | No | `true` |
| `SHOW_DAYS_OF_WEEK` | Show most productive days | No | `true` |
| `COMMIT_MESSAGE` | Custom commit message | No | `'docs(stats): update github stats'` |
| `COMMIT_BY_ME` | Whether commits should be authored by token owner | No | `false` |
| `COMMIT_USERNAME` | Username for commit author | No | `'github-actions[bot]'` |
| `COMMIT_EMAIL` | Email for commit author | No | `'41898282+github-actions[bot]@users.noreply.github.com'` |

## License

MIT License - see [LICENSE](LICENSE) for details.