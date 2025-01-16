# Python Simple ESC/POS API

This repository provides two main classes to simplify printing operations on an Epson TM-T20 (or compatible) thermal receipt printer over USB. It uses the [python-escpos](https://python-escpos.readthedocs.io/en/latest/) library under the hood to manage low-level printing commands.

---

## Table of Contents
- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic POS Printing](#basic-pos-printing)
  - [Buffered Printing (POSPrinterGraphics)](#buffered-printing-posprintergraphics)
  - [Examples](#examples)
- [API Reference](#api-reference)
  - [POSPrinter](#posprinter)
  - [POSPrinterGraphics](#posprintergraphics)
- [License](#license)

---

## Introduction

The **POSPrinter** class is a thin wrapper around `escpos` functionality, adding automatic reconnection and error handling. This makes it more resilient in environments where the printer might be disconnected or powered off.

The **POSPrinterGraphics** class builds on top of **POSPrinter**, buffering commands before they're actually printed. This is useful if you want to construct a complex printout (with text, lines, charts, tables, etc.) and then print everything at once or at specific intervals.

---

## Requirements

- **Python 3.7+** (due to type annotations and f-strings usage)
- **python-escpos** (specifically, the [escpos](https://pypi.org/project/escpos/) package)
- **libusb** (if you are using USB printers on some environments)

---

## Installation

1. Clone this repository or copy the relevant classes into your project.
2. Install the dependencies:
   ```bash
   pip install escpos
   ```
3. Ensure you have the necessary system dependencies for USB printing (e.g., `libusb`).

---

## Usage

Below are a couple of ways to utilize this API.

### Basic POS Printing

```python
from your_module import POSPrinter

# Create an instance of POSPrinter
printer = POSPrinter()

# Print a simple text
printer.print("Hello, world!")

# Print a line of '#' characters the width of the printer
printer.line()

# Feed the paper by 2 lines
printer.feed(2)

# Cut the paper
printer.cut()
```

**Key Points**:
- The printer automatically attempts to reconnect if any command fails (`do_safe` method).
- You can call `printer.set_upside_down(True)` if you want to enable upside-down printing.
- You can customize text size, justification, smoothing, etc.

### Buffered Printing (POSPrinterGraphics)

The **POSPrinterGraphics** class buffers commands in memory. When `print()` or `print_cut()` is called, it either prints them in the order they were added or in reverse order if upside-down printing is enabled.

```python
from your_module import POSPrinter, POSPrinterGraphics

# Create the printer and the buffered "graphics" object
printer = POSPrinter()
printer_graphics = POSPrinterGraphics(printer, width=48, upside_down=False)

# Add some commands to the buffer
printer_graphics.text("My Receipt Title", justify="center", size=2)
printer_graphics.line()
printer_graphics.text("Item A: $1.00", justify="left")
printer_graphics.text("Item B: $2.50", justify="left")
printer_graphics.line()

# Print them all at once
printer_graphics.print()

# Optionally, cut afterwards
printer_graphics.cut()
```

**Key Points**:
- You can keep adding commands (e.g., `text()`, `line()`, `justify()`) to the buffer.
- If `upside_down` is `True`, all buffered commands are reversed right before printing, simulating an upside-down print.

### Examples

#### Printing a Chart

```python
# Suppose we have some numeric data
data_points = [2, 5, 9, 8, 5, 3, 7, 10, 9, 6]

# Create the "graphics" printer
printer_graphics = POSPrinterGraphics(printer, width=48, upside_down=False)

# Print a simple chart with height=10 lines
printer_graphics.print_chart(data_points, height=10)

# Finally, print and cut
printer_graphics.print_cut()
```

#### Printing a Table

```python
table_data = [
    ("Name", "Jane Doe"),
    ("Age", 29),
    ("City", "San Francisco"),
    ("Occupation", "Engineer"),
]

printer_graphics = POSPrinterGraphics(printer, width=48)
printer_graphics.print_table(table_data, padding=1)
printer_graphics.print_cut()
```

---

## API Reference

### POSPrinter

```python
class POSPrinter:
    def __init__(self):
        ...
```

**Methods**:

1. **connect()**  
   Attempts to establish a USB connection with the printer. If `last_upside_down` is `True`, it re-enables upside-down mode.

2. **do_safe(func, *args, **kwargs)**  
   A helper to run printer commands within a `try/except` block, automatically reconnecting and retrying if an exception occurs.

3. **cut(feed: int = 2)**  
   Issues a paper cut command, optionally feeding a number of lines first.

4. **print(text: str, justify: str = None)**  
   Prints the given text. Justification can be `"left"`, `"center"`, or `"right"`.

5. **feed(lines: int = 1)**  
   Feeds the paper by the specified number of lines.

6. **line(symbol: str = None)**  
   Prints a line made up of a specified symbol (defaults to `"#"`).

7. **justify(side: str)**  
   Sets justification: `"left"`, `"center"`, or `"right"`.

8. **set_text_size(width: int = 0, height: int = 0)**  
   Adjusts text size (width and height multipliers).

9. **set_upside_down(upside_down: bool = True)**  
   Toggles upside-down printing mode.

10. **set_smooth(smooth: bool = True)**  
    Toggles smoothing mode for text.

---

### POSPrinterGraphics

```python
class POSPrinterGraphics:
    def __init__(self, printer: POSPrinter, width: int = 48, upside_down: bool = False):
        ...
```

**Methods**:

1. **text(text: str, justify: str = None, size: int = None)**  
   Buffers a text command.  
   - `justify`: `"left"`, `"center"`, or `"right"`.  
   - `size`: Optionally set a larger text size (1–8).

2. **feed(lines: int = 1)**  
   Buffers a feed command.

3. **line()**  
   Buffers a line of `#` characters matching the printer width.

4. **justify(side: str)**  
   Buffers a justification change.

5. **cut()**  
   Buffers a cut command.

6. **set_text_size(width: int = 0, height: int = 0)**  
   Buffers a text size change.

7. **print()**  
   Executes all buffered commands in the correct order (reversed if `upside_down=True`) and clears the buffer.

8. **print_cut()**  
   Combines `print()` + `cut()` at once.

9. **print_chart(values, height: int = 10)**  
   Buffers commands that generate a simple bar-like chart from the given list of numeric `values`.

10. **print_table(data: list[tuple[Any, Any]], padding: int = 0)**  
    Buffers a simple table-like structure, aligning values according to the given width.

---

## License

This code is provided as-is under an open-source license (e.g., MIT). Feel free to modify and use it in your own projects. See the [LICENSE](LICENSE) file for details (if included).

---

**Note**:  
- For more robust or production-scale solutions, consider additional error handling, advanced formatting, or spooler integration.  
- Refer to the [python-escpos docs](https://python-escpos.readthedocs.io/en/latest/) for in-depth configurations like character encoding, barcode printing, and more.