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

## Setup

1. Clone the repository
2. Create a `.env` file:
```env
INPUT_GH_TOKEN=your_github_personal_access_token
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run locally:
```bash
python github_stats.py <username>
```

### Required Permissions

You'll need a [GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) with:
- `repo` scope for repository access
- `user` scope for user data access

## Usage as GitHub Action

1. Create `.github/workflows/github-stats.yml`:
```yaml
name: GitHub Stats Update
on:
schedule:
cron: '0 0 ' # Runs daily at midnight
workflow_dispatch: # Allows manual trigger
jobs:
update-stats:
runs-on: ubuntu-latest
steps:
uses: VatsalSy/commits-readme-stats@v1.0.0
with:
GH_TOKEN: ${{ secrets.GH_TOKEN }}
SHOW_COMMIT: true
SHOW_DAYS_OF_WEEK: true
COMMIT_MESSAGE: 'docs(stats): update github stats'
```


2. Add `GH_TOKEN` to your repository secrets with the required permissions.

3. Add these markers to your README.md where you want the stats to appear:

```markdown
<!--START_SECTION:github-stats-->
<!--END_SECTION:github-stats-->
```



## License

MIT License - see [LICENSE](LICENSE) for details.
