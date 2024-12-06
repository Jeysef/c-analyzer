#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define MAX_CONTACTS 42 // Minimum number of contacts
#define MAX_LENGTH 102  // 100 chars + '\0'

typedef struct
{
  char name[MAX_LENGTH];
  char number[MAX_LENGTH];
} Contact;

Contact contacts[MAX_CONTACTS];
int contact_count = 0;

const char *mappedChars[] = {"+", "", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"};

void to_lower(char *str)
{
  for (int i = 0; str[i]; i++)
  {
    str[i] = (char)tolower(str[i]);
  }
}

void trim(char *str)
{
  size_t len = strlen(str);
  char *end = str + len - 1;
  while (len > 0 && (*end == '\n' || *end == '\r'))
  {
    --end;
    str[--len] = '\0';
  }
}

void read_contacts()
{
  char line[MAX_LENGTH];
  while (contact_count < MAX_CONTACTS)
  {
    // Read name
    if (fgets(line, sizeof(line), stdin) == NULL)
      break;
    trim(line);
    if (strlen(line) == 0)
      continue; // Skip empty lines
    strncpy(contacts[contact_count].name, line, MAX_LENGTH - 1);
    contacts[contact_count].name[MAX_LENGTH - 1] = '\0';
    // Read number
    if (fgets(line, sizeof(line), stdin) == NULL)
      break;
    trim(line);
    if (strlen(line) == 0)
      continue; // Skip empty lines
    strncpy(contacts[contact_count].number, line, MAX_LENGTH - 1);
    contacts[contact_count].number[MAX_LENGTH - 1] = '\0';

    contact_count++;
  }
}

void contacts_to_lower()
{
  for (int i = 0; i < contact_count; i++)
  {
    to_lower(contacts[i].name);
    to_lower(contacts[i].number);
  }
}

void printContacts()
{
  for (int i = 0; i < contact_count; i++)
  {
    printf("%s, %s\n", contacts[i].name, contacts[i].number);
  }
}

bool is_match_complex(const char *str, const char *query)
{
  while (*str)
  {
    if (*query == '\0')
      return true; // Found a match

    if (isdigit(*str))
    {
      if (*str == *query)
      {
        query++;
      }
    }
    else
    {
      const int qNum = *query - '0';
      if ((qNum >= 0 && qNum <= 9) && strchr(mappedChars[qNum], *str))
      {
        query++;
      }
    }

    str++;
  }
  return *query == '\0';
}

bool is_match_unbroken(const char *str, const char *query)
{
  // search for unbroken sequence

  while (*str)
  {
    const char *q = query;
    const char *s = str;
    // printf("*q: %c, *s: %c \n", *q, *s);
    while (*q && *s)
    {
      // printf("comparing cont. *q: %c, *s: %c \n", *q, *s);
      if (isdigit(*s))
      {
        // int digit = *s - '0';
        if (*s == *q)
        {
          // printf("are equal\n");
          q++;
          s++;
        }
        else
        {
          break;
        }
      }
      else
      {
        const int qNum = *q - '0';
        if ((qNum >= 0 && qNum <= 9) && strchr(mappedChars[qNum], *s))
        {
          // printf("comparing cont. *q: %s, *s: %c \n", mappedChars[qNum], *s);
          q++;
          s++;
        }
        else
        {
          break;
        }
      }
    }

    if (*q == '\0')
      return true;
    str++;
  }
  return *query == '\0';
}

// pointer to is_match_unbroken function named is_match
bool (*is_match)(const char *str, const char *query) = is_match_unbroken;

void search_contacts(const char *query)
{
  bool found = false;
  for (int i = 0; i < contact_count; i++)
  {
    if (is_match(contacts[i].name, query) || is_match(contacts[i].number, query))
    {
      printf("%s, %s\n", contacts[i].name, contacts[i].number);
      found = true;
    }
  }
  if (!found)
  {
    printf("Not found\n");
  }
}

bool isValidQuery(const char *query)
{
  while (*query)
  {
    if (!isdigit(*query))
    {
      return false;
    }
    query++;
  }
  return true;
}

int main(int argc, char **argv)
{
  int sflag = 0;
  int optind = 1;

  read_contacts();
  contacts_to_lower();
  if (argc == optind)
  {
    printContacts();
  }
  else if (argc == optind + 1)
  {
    const char *query = argv[optind];
    if (!isValidQuery(query))
    {
      fprintf(stderr, "Invalid query\n");
      return 1;
    }
    if (sflag)
    {
      is_match = is_match_complex;
    }
    search_contacts(query);
  }
  else
  {
    fprintf(stderr, "Usage: %s [-s] [CISLO] <[FILE]\n", argv[0]);
    return 1;
  }

  return 0;
}
