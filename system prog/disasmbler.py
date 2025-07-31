form1 = {
    0xC4: "FIX",
    0xC0: "FLOAT",
    0xF4: "HIO",
    0xC8: "NORM",
    0xF0: "SIO",
    0xF8: "TIO",
}

form3 = {
    0x18: "ADD",
    0x40: "AND",
    0x28: "COMP",
    0x24: "DIV",
    0x3C: "J",
    0x30: "JEQ",
    0x34: "JGT",
    0x38: "JLT",
    0x48: "JSUB",
    0x00: "LDA",
    0x50: "LDCH",
    0x08: "LDL",
    0x04: "LDX",
    0x20: "MUL",
    0x44: "OR",
    0xD8: "RD",
    0x4C: "RSUB",
    0x0C: "STA",
    0x54: "STCH",
    0x14: "STL",
    0xE8: "STSW",
    0x10: "STX",
    0x1C: "SUB",
    0xE0: "TD",
    0x2C: "TIX",
    0xDC: "WD",
}

def read_records(file_path):
    with open(file_path) as f:
        h = f.readline()
        if h[0] != 'H':
            exit()

        name = h[1:7]
        start_add = int(h[7:13], 16)
        size = int(h[13:19], 16)

        t_records = []
        while True:
            rec = f.readline()
            if not rec or rec[0] != 'T':
                break
            t_records.append(rec)

        if rec[0] != 'E':
            exit()

    return name, start_add, size, t_records

def process_t_records(name, start_add, size, t_records):
    symbols = {}
    loc = start_add
    symbol = 1

    for t in t_records:
        if t != t_records[0] and int(t[1:7], 16) > t_end:
            loc += (int(t[1:7], 16) - t_end)
        t_start = int(t[1:7], 16)
        t_len = int(t[7:9], 16)
        t_end = t_start + t_len
        instructions = t[9:2 * t_len + 9]

        while len(instructions) > 0:
            if len(instructions) == 2:
                instructions = instructions[2:]
                continue

            opcode = int(instructions[0:2], 16)
            addr = int(instructions[2:6], 16)

            if opcode - 1 in form3 and opcode >> 0 & 1:
                imm = 1
                opcode -= 1
            else:
                imm = 0

            form = 0
            if opcode in form1:
                form = 1
            elif opcode in form3:
                form = 3
            else:
                instructions = instructions[2:]
                loc += 1
                continue

            if opcode in form3 and addr >> 15 & 1:
                addr = int(hex(addr - 0x8000), 16)

            if not (opcode in form3 and form3[opcode] == "RSUB") and not (
                    start_add <= addr <= start_add + size
            ):
                form = 0

            if form == 0:
                instructions = instructions[6:]
                loc += 3
                continue

            if opcode in form1:
                instructions = instructions[2:]
                loc += 1
            elif opcode in form3:
                if form3[opcode] != "RSUB":
                    symbols[addr] = f"SMBL{symbol}"
                    symbol += 1
                instructions = instructions[6:]
                loc += 3
            else:
                instructions = instructions[2:]
                loc += 1

    return symbols

def write_symbols(symbols, output_path='symbol.txt'):
    with open(output_path, 'w+') as f:
        for key, value in symbols.items():
            f.write(f"{format(key, 'x')} : {value}\n")

def create_assembly_file(name, start_add, symbols, t_records, output_path='assembly.txt'):
    with open(output_path, 'w+') as f:
        ctr = 3
        f.write(f"{ctr:<6}{name:<6} START {format(start_add, 'x').rjust(6, '0')}\n")      

        loc = start_add
        for t in t_records:
            if t != t_records[0] and int(t[1:7], 16) > t_end:
                ctr += 3
                if loc in symbols:
                    f.write(
                        f"{ctr:<6} {symbols[loc]:<6} RESB {int(t[1:7], 16) - t_end}\n"           #f.write(f"{format(ctr, 'x'):<6} {symbols[loc]:<7} {form3[opcode]}\n")
                    )
                else:
                    f.write(f"{ctr:<6} RESB {int(t[1:7], 16) - t_end}\n")
                loc += (int(t[1:7], 16) - t_end)

            t_start = int(t[1:7], 16)
            t_len = int(t[7:9], 16)
            t_end = t_start + t_len
            instructions = t[9:2 * t_len + 9]

            while len(instructions) > 0:
                bytes = []
                if len(instructions) == 2:
                    ctr += 3
                    if loc in symbols:
                        f.write(
                            f"{ctr:<6} {symbols[loc]:<6} BYTE {instructions[0:2]}\n"
                        )
                    else:
                        f.write(f"{ctr:<6} BYTE {instructions[0:2]}\n")
                    instructions = instructions[2:]
                    loc += 1
                    continue

                opcode = int(instructions[0:2], 16)
                addr = int(instructions[2:6], 16)
                x = 0

                if (opcode - 1) in form3 and (addr & 0x8000) != 0:
                    x = 1
                    addr = addr - 0x8000

                if (
                    not (form3.get(opcode) and form3[opcode] == "RSUB")
                    and not (start_add <= addr <= start_add + size)
                ):
                    bytes.append(instructions[0:6])
                    instructions = instructions[6:]
                    loc += 3
                    continue

                if form3.get(opcode) and form3[opcode] == "RSUB":
                    ctr += 3
                    if loc in symbols:
                        f.write(f"{ctr:<6} {symbols[loc]:<7} {form3[opcode]}\n")
                    else:
                        f.write(f"{ctr:<6} {form3[opcode]}\n")
                else:
                    if x == 1:
                        ctr += 3
                        if loc in symbols:
                            f.write(
                                f"{ctr:<6} {symbols[loc]:<7} {form3[opcode]} {symbols[addr]}, X\n"
                            )
                        else:
                            f.write(
                                f"{ctr:<6} {form3[opcode]} {symbols[addr]}, X\n"
                            )
                    else:
                        ctr += 3
                        if loc in symbols:
                            f.write(
                                f"{ctr:<6} {symbols[loc]:<7} {form3[opcode]} {symbols[addr]}\n"
                            )
                        else:
                            f.write(f"{ctr:<6} {form3[opcode]} {symbols[addr]}\n")

                instructions = instructions[6:]
                loc += 3

if __name__ == "__main__":
    hte_file_path = 'hte.txt'

    name, start_add, size, t_records = read_records(hte_file_path)
    symbols = process_t_records(name, start_add, size, t_records)

    symbols_output_path = 'symbols.txt'
    write_symbols(symbols, symbols_output_path)

    assembly_output_path = 'assembly.txt'
    create_assembly_file(name, start_add, symbols, t_records, assembly_output_path)
