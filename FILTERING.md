# Advanced Job Filtering

This feature allows users to filter job notifications using multiple criteria to receive only the job postings that match their interests.

## How It Works

The bot offers a comprehensive filtering system with two main types of filters:

1. **Job Type Filters**: Automatically categorizes jobs into predefined types based on job title and description content.
2. **Custom Keyword Filters**: Allows users to define custom text filters that match against job titles and descriptions.

Users can combine multiple job types and custom keywords to create a personalized filtering experience.

## Available Job Types

The system currently recognizes the following job types:

- `fullstack`: Full Stack development positions
- `frontend`: Frontend/UI development positions
- `backend`: Backend development positions
- `mobile`: Mobile development (iOS, Android, React Native, etc.)
- `devops`: DevOps, SRE, and infrastructure positions
- `blockchain`: Blockchain, smart contract, and web3 positions
- `ai`: Artificial Intelligence and Machine Learning positions
- `data`: Data engineering, analysis, and database positions
- `design`: UI/UX design positions
- `product`: Product management positions
- `qa`: Quality assurance and testing positions
- `other`: Any jobs that don't fit the above categories

## User Commands

- `/filter` or `/filters`: Opens the filter management menu with the following options:
  - **View My Filters**: Shows all your active filters
  - **Add Job Type Filter**: Add a filter based on predefined job categories
  - **Add Custom Filter**: Add a custom keyword filter
  - **Remove Filter**: Remove a specific filter
  - **Clear All Filters**: Reset all filtering preferences

## Filter Logic

- Multiple job type filters use an **OR** condition: A job matches if it belongs to ANY of the specified job types.
- Multiple custom keyword filters use an **OR** condition: A job matches if it contains ANY of the custom keywords.
- Between job types and custom filters, an **OR** condition applies: A job matches if it satisfies EITHER filter category.

## Implementation Details

- Job type detection is implemented in the `Job` class in `src/rss_parser.py`
- User filter preferences are stored in `user_filters.json` or in Redis
- The filtering system is implemented in `src/filters.py`
- Filter application happens in `check_new_jobs` function in `src/bot.py`