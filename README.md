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
</p>


<p align="center">
   Are you an early 🐤 or a night 🦉?
   <br/>
   When are you most productive during the day?
   <br/>
   Let's analyze your commit patterns!
</p>

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

## License

MIT License - see [LICENSE](LICENSE) for details.
