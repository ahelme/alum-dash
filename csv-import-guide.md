# AlumDash CSV Import Guide

This guide explains how to prepare and import alumni data using CSV files in AlumDash.

## Quick Start

1. **Download the template**: Click "Download Template" in the Import CSV section
2. **Fill in your data**: Add your alumni information following the format below
3. **Upload the file**: Drag and drop or click to select your completed CSV file
4. **Review results**: Check the import statistics and fix any errors if needed

## CSV Format Requirements

### Required Columns

Your CSV file **must** include these columns with exact names:

| Column Name | Description | Example |
|-------------|-------------|---------|
| `name` | Full name of the alumni (max 100 characters) | "Sarah Chen" |
| `graduation_year` | Year of graduation (1970-2030) | 2020 |
| `degree_program` | Must be one of the valid programs (see below) | "Film Production" |

### Valid Degree Programs

Use exactly one of these values in the `degree_program` column:
- `Film Production`
- `Screenwriting`
- `Animation`
- `Documentary`
- `Television`

### Optional Columns

You can include any or all of these optional columns:

| Column Name | Description | Example |
|-------------|-------------|---------|
| `email` | Valid email address | "sarah.chen@example.com" |
| `linkedin_url` | LinkedIn profile URL | "https://linkedin.com/in/sarahchen" |
| `imdb_url` | IMDb profile URL | "https://www.imdb.com/name/nm1234567" |
| `website` | Personal website URL | "https://sarahchenfilms.com" |

## Sample CSV File

```csv
name,graduation_year,degree_program,email,linkedin_url,imdb_url,website
John Smith,2020,Film Production,john.smith@example.com,https://linkedin.com/in/johnsmith,https://www.imdb.com/name/nm1234567,https://johnsmithfilms.com
Jane Doe,2021,Documentary,jane.doe@example.com,,,
Michael Johnson,2019,Animation,m.johnson@example.com,https://linkedin.com/in/mjohnson,,
Sarah Williams,2018,Screenwriting,s.williams@example.com,,,https://sarahwrites.com
David Brown,2022,Television,,,https://www.imdb.com/name/nm7654321,
```

## Validation Rules

### Name
- **Required**: Cannot be empty
- **Length**: Maximum 100 characters
- **Format**: Any text is accepted

### Graduation Year
- **Required**: Cannot be empty
- **Range**: Must be between 1970 and 2030
- **Format**: Must be a valid 4-digit number

### Degree Program
- **Required**: Cannot be empty
- **Values**: Must exactly match one of the valid degree programs
- **Case sensitive**: Use exact capitalization as shown above

### Email (Optional)
- **Format**: Must be a valid email address with @ symbol
- **Example**: "user@domain.com"
- **Empty**: Leave blank if not available

### URLs (Optional)
- **Format**: Must start with `http://` or `https://`
- **LinkedIn**: Should be a LinkedIn profile URL
- **IMDb**: Should be an IMDb name page URL
- **Website**: Any valid website URL
- **Empty**: Leave blank if not available

## Common Errors and Solutions

### Validation Errors

**"Missing required columns"**
- Ensure your CSV has columns named exactly: `name`, `graduation_year`, `degree_program`
- Column names are case-sensitive

**"Invalid degree program"**
- Check that the degree program matches exactly one of the valid options
- Common mistake: "film production" should be "Film Production"

**"Invalid graduation year"**
- Ensure the year is between 1970 and 2030
- Make sure it's a number, not text

**"Invalid email format"**
- Email must contain @ symbol and a domain
- Example: "user@example.com" not "user.example.com"

**"URL must start with http:// or https://"**
- Add the protocol prefix to all URLs
- Example: "https://linkedin.com/in/username" not "linkedin.com/in/username"

### Import Errors

**"Alumni already exists"**
- The system checks for duplicates based on name and graduation year
- If someone with the same name and graduation year exists, the import will skip that record

**"Name too long"**
- Alumni names must be 100 characters or less
- Consider abbreviating very long names

## File Requirements

- **Format**: Must be a .csv file
- **Size**: Maximum 10MB per file
- **Encoding**: UTF-8 (standard for most spreadsheet applications)
- **Separators**: Comma-separated values (standard CSV format)

## Creating CSV Files

### From Excel or Google Sheets
1. Enter your data in the spreadsheet with column headers
2. Save/Export as CSV format
3. Choose UTF-8 encoding if prompted

### From Text Editor
1. Create a new text file
2. Add the column headers as the first line
3. Add data rows, separating values with commas
4. Save with .csv extension

## Import Process

1. **Upload**: The system validates your CSV format first
2. **Validation**: Checks all required columns and data formats
3. **Processing**: Imports valid records and reports any errors
4. **Results**: Shows statistics and lists any failed records

## Best Practices

### Data Preparation
- **Clean your data**: Remove extra spaces, fix typos
- **Consistent formatting**: Use the same date and URL formats throughout
- **Test with small batches**: Try importing a few records first
- **Backup**: Keep a copy of your original data

### Quality Control
- **Download the template**: Use the provided template as your starting point
- **Validate URLs**: Check that LinkedIn, IMDb, and website URLs are working
- **Check for duplicates**: Review your data for potential duplicate entries
- **Verify degree programs**: Ensure all degree programs match the valid options exactly

### Troubleshooting
- **Review error messages**: The system provides specific error details for each failed record
- **Fix and re-import**: Correct errors in your CSV and import again
- **Partial imports**: Successfully imported records won't be duplicated if you re-import

## Import History

The system keeps a complete log of all import attempts, including:
- Filename and timestamp
- Total records processed
- Number of successful and failed imports
- Detailed error information

Access this information in the "Import History" section to track your import progress and troubleshoot issues.

## Getting Help

If you encounter issues not covered in this guide:
1. Check the import history for detailed error messages
2. Verify your CSV format against the template
3. Test with a smaller sample of your data
4. Contact support with specific error messages and your CSV file structure

## Example Template

Download the CSV template from the application for a ready-to-use file with the correct column headers and sample data.