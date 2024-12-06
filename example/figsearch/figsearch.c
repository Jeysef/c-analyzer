#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  unsigned x;  // column, 0-based
  unsigned y;  // row, 0-based
} Point;

typedef struct {
  Point start;
  Point end;
} Line;

typedef struct {
  unsigned width;
  unsigned height;
  bool data[];  // 0 = white, 1 = black
} Bitmap;

Bitmap *create_bitmap(unsigned width, unsigned height) {
  size_t size = sizeof(Bitmap) + width * height * sizeof(bool);
  Bitmap *bitmap = (Bitmap *)malloc(size);
  if (bitmap) {
    bitmap->width = width;
    bitmap->height = height;
  }
  return bitmap;
}

void free_bitmap(Bitmap *bitmap) {
  free(bitmap);
}

Bitmap *load_bitmap(const char *filename) {
  FILE *file = fopen(filename, "r");
  if (!file) {
    fprintf(stderr, "File not found\n");
    return NULL;
  };

  unsigned width, height;
  if (fscanf(file, "%u %u", &height, &width) != 2) {
    fclose(file);
    fprintf(stderr, "Invalid file format\n");
    return NULL;
  }

  if (width <= 0 || height <= 0) {
    fclose(file);
    fprintf(stderr, "Invalid bitmap size\n");
    return NULL;
  }

  Bitmap *bitmap = create_bitmap(width, height);
  if (!bitmap) {
    fclose(file);
    fprintf(stderr, "Memory allocation failed\n");
    return NULL;
  }

  const unsigned bitmap_area = width * height;
  for (unsigned index = 0; index < bitmap_area; index++) {
    int pixel;
    if (fscanf(file, "%d", &pixel) != 1 || (pixel != 0 && pixel != 1)) {
      free_bitmap(bitmap);
      fclose(file);
      fprintf(stderr, "Invalid pixel value\n");
      return NULL;
    }
    bitmap->data[index] = pixel;
  }

  fclose(file);
  return bitmap;
}

void print_help() {
  printf("Usage: figsearch COMMAND [FILE]\n");
  printf("Commands:\n");
  printf("  --help   Display this help message\n");
  printf("  test     Check if the file contains valid bitmap\n");
  printf("  hline    Find longest horizontal line\n");
}

int test_bitmap(const char *filename) {
  Bitmap *bitmap = load_bitmap(filename);
  if (!bitmap) return 1;
  free_bitmap(bitmap);
  return 0;
}

unsigned hline_length(Point start, Point end) { return end.x - start.x + 1; }

int find_hline(Bitmap *bitmap, Line *line) {
  Point start_final;
  Point end_final;
  unsigned length_final = 0;
  for (unsigned y = 0; y < bitmap->height; y++) {
    for (unsigned x = 0; x < bitmap->width - length_final; x++) {
      unsigned index = y * bitmap->width + x;
      if (bitmap->data[index]) {
        Point start = {x, y};
        Point end = {x, y};
        for (unsigned i = x + 1; i < bitmap->width; i++) {
          unsigned look_index = y * bitmap->width + i;
          if (!bitmap->data[look_index]) {
            x = i;
            break;
          }
          end.x = i;
        }
        unsigned current_length = hline_length(start, end);
        if (!length_final || current_length > length_final) {
          start_final = start;
          end_final = end;
          length_final = current_length;
        }
      }
    }
  }
  if (length_final) {
    line->start = start_final;
    line->end = end_final;
    return 0;
  }
  return 1;
}

void print_line(Line *line) {
  printf("%u %u %u %u\n", line->start.y, line->start.x, line->end.y, line->end.x);
}

const char *get_filename(int argc, char const *argv[]) {
  if (argc > 2) return argv[2];
  return NULL;
}

int main(int argc, char const *argv[]) {
  if (argc < 2 || argc > 3) {
    fprintf(stderr, "Invalid arguments\n");
    return 1;
  }

  if (strcmp(argv[1], "--help") == 0) {
    print_help();
    return 0;
  }

  const char *filename = get_filename(argc, argv);

  if (strcmp(argv[1], "test") == 0) {
    if (!filename) {
      fprintf(stderr, "Filename required\n");
      return 1;
    }
    return test_bitmap(filename);
  }

  if (strcmp(argv[1], "hline") == 0) {
    if (!filename) {
      fprintf(stderr, "Filename required\n");
      return 1;
    }
    Bitmap *bitmap = load_bitmap(filename);
    if (!bitmap) {
      return 1;
    }
    Line line;
    int result = find_hline(bitmap, &line);
    free_bitmap(bitmap);
    if (result == 0) {
      print_line(&line);
      return 0;
    }
    fprintf(stderr, "No line found\n");
    return 1;
  }

  fprintf(stderr, "Invalid command\n");
  return 1;
}
