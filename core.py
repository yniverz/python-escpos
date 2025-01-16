import math
import time
import traceback
from typing import Any, Callable
from escpos import USBConnection
from escpos.impl.epson import TMT20

class POSPrinter:
    def __init__(self):
        self.usb_dev = None
        self.printer = None

        self.printer_width = 48
        self.line_char = "#"
        self.last_upside_down = False
        self.do_safe(self.connect)


    def connect(self):
        self.usb_dev = USBConnection.create("04b8:0e28,interface=0,ep_out=1,ep_in=82")
        if self.printer is not None:
            self.printer.__init__(self.usb_dev)
        else:
            self.printer = TMT20(self.usb_dev)
        self.printer.init()

        if self.last_upside_down:
            self.do_safe(self.set_upside_down, self.last_upside_down)

    def do_safe(self, func, *args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(traceback.format_exc())
                print("waiting 20 seconds...")
                time.sleep(20)

                print("reconnecting...")
                if func != self.connect:
                    self.do_safe(self.connect)


    def cut(self, feed: int=2):
        self.do_safe(self.printer.cut, feed=feed)

    def print(self, text: str, justify: str=None):
        if justify:
            self.justify(justify)

        self.do_safe(self.printer.text, text)

        if justify:
            self.justify("left")

    def feed(self, lines: int = 1):
        self.do_safe(self.printer.lf, lines)

    def line(self, symbol=None):
        if not symbol:
            symbol = self.line_char
        self.print(symbol*self.printer_width)

    def justify(self, side):
        if side == "left":
            self.do_safe(self.printer.justify_left)
        elif side == "center":
            self.do_safe(self.printer.justify_center)
        elif side == "right":
            self.do_safe(self.printer.justify_right)
        else:
            raise ValueError("Invalid side")
        
    def set_text_size(self, width: int = 0, height: int = 0):
        self.do_safe(self.printer.set_text_size, width, height)
        
    def set_upside_down(self, upside_down: bool = True):
        self.do_safe(self._set_upside_down, upside_down)
        
    def _set_upside_down(self, upside_down: bool = True):
        # ESC { n
        self.printer.device.write(b'\x1B' + b'{1' if upside_down else b'{2')
        self.last_upside_down = upside_down

    def set_smooth(self, smooth: bool = True):
        self.do_safe(self._set_smooth, smooth)

    def _set_smooth(self, smooth: bool = True):
        # GS b n
        self.printer.device.write(b'\x1D' + b'b' + b'\x01' if smooth else b'\x02')


class POSPrinterGraphics:
    def __init__(self, printer: POSPrinter, width: int = 48, upside_down: bool = False):
        self.printer = printer
        self.width = width

        self.upside_down = upside_down
        self.printer.set_upside_down(upside_down)
        self.command_buffer: list[tuple[Callable, list]] = []


    def text(self, text: str, justify: str=None, size: int = None):
        if size:
            if self.upside_down:
                self.set_text_size()
            else:
                self.set_text_size(size, size)
        self.command_buffer.append((self.printer.print, [text, justify]))
        if size:
            if self.upside_down:
                self.set_text_size(size, size)
            else:
                self.set_text_size()

    def feed(self, lines: int = 1):
        self.command_buffer.append((self.printer.feed, [lines]))

    def line(self):
        self.command_buffer.append((self.printer.line, []))

    def justify(self, side):
        self.command_buffer.append((self.printer.justify, [side]))

    def cut(self):
        self.command_buffer.append((self.printer.cut, []))

    def set_text_size(self, width: int = 0, height: int = 0):
        self.command_buffer.append((self.printer.set_text_size, [width, height]))

    def print_cut(self):
        self.print()
        self.printer.cut()

    def print(self):
        if self.upside_down:
            self.command_buffer.reverse()

        for command, args in self.command_buffer:
            command(*args)

        self.command_buffer.clear()




    def print_chart(self, values, height: int = 10):
        width = self.width - 2
        interpolated_values = []
        if len(values) >= width:
            interpolated_values = [values[i] for i in range(0, len(values), len(values) // width)]
        else:
        # add interpolated values. make it the same width as the datapoints value
            for i in range(width):
                # get the index of the value in the original list
                index = i * (len(values) - 1) / (width - 1)
                # get the two values to interpolate
                a = math.floor(index)
                b = math.ceil(index)
                # get the weight of the interpolation
                weight = index - a
                # interpolate the values
                interpolated_values.append(values[a] * (1 - weight) + values[b] * weight)


        # map height to the range of values
        max_value = max(interpolated_values)
        min_value = min(interpolated_values)
        range_value = max_value - min_value

        # map values to the range of height
        chart = []
        for value in interpolated_values:
            chart.append(int((value - min_value) / range_value * (height)))

        # compile strings
        # chart_str = ""
        chart_lines = []
        for y in range(height, -1, -1):
            chart_str = ""
            for x in range(width):
                if chart[x] == y:
                    chart_str += "*"
                else:
                    chart_str += " "
            if y != 1:
                # chart_str += "\n"
                chart_lines.append(chart_str)

        # print(chart)

        # # go through and fill jumps
        # for x in range(width, 1, -1):
        #     difference = chart[x] - chart[x - 1]
        #     line_index = height - chart[x]
        #     if difference > 1:
        #         for i in range(1, difference - 1):
        #             chart_lines[line_index + i] = chart_lines[line_index + i][:x-1] + "*" + chart_lines[line_index + i][x:]

        #     if difference < -1:
        #         for i in range(1, -(difference + 1)):
        #             chart_lines[line_index - i] = chart_lines[line_index - i][:x-1] + " " + chart_lines[line_index - i][x:]


        # self.line()
        self.text("+" + "-" * (width) + "+")
        for line in chart_lines:
            self.text("|" + line + "|")
        # self.line()
        self.text("+" + "-" * (width) + "+")

    def print_table(self, data: list[tuple[Any, Any]], padding: int = 0):
        # for key, value in data:
        #     lable_len = len(str(key))
        #     # self.printer.print(f"{key}: {value:>{self.width-lable_len-2}}")
        #     self.text(f"{key}: {value:>{self.width-lable_len-2}}")

        for key, value in data:
            lable_len = len(str(key))
            self.text(" " * padding + f"{key}: {value:>{self.width-lable_len-2-(2*padding)}}")
