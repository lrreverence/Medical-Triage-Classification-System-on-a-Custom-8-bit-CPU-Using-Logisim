import tkinter as tk
from tkinter import filedialog, messagebox

# Assembler dictionary for opcodes and their values
opcodes = {
            "NOP": "00", "LIA": "01", "LIB": "02", "LIT": "03", "LDA": "10", "LDB": "11", "LDT": "12", "LD0": "13", "LD1": "14", "LDI": "15",
            "STA": "20", "STB": "21", "STK": "22", "STI": "23", 
            "ADD": "30", "SUB": "31", "RTR": "32", "RTL": "33", "CMP": "34",  "NOT": "35" , "AND": "36" , "OR": "37", "XOR": "38" , "RVA": "50", "RVD": "51", "UPD": "52", "JMP": "70",
            "JPC": "71", "JPB": "72", "JNZ": "73", "JPZ": "74", "JPG": "75",
            "JPE": "76", "JPL": "77", "JCAL": "78", "RET": "79","JCL": "7A", "JCE": "7B", "JCG": "7C" , "JPI": "7D",      }



# Helper function to convert a string into LIT instructions
def convert_string_to_lit(string):
    lit_instructions = []
    for char in string:
        ascii_value = f"{ord(char):02X}"  # Convert char to 2-digit hex ASCII
        lit_instructions.append('03')     # LIT opcode for loading immediate into TTY
        lit_instructions.append(ascii_value)
    return lit_instructions
# Dictionary to store variables and their memory addresses
variables = {}
next_available_address = 0xFFFF  # Start variable storage at address 0xFFFF

# Helper function to allocate memory for a variable
def allocate_variable(name, value):
    
    global next_available_address
    if next_available_address < 0x0000:
        raise Exception("Out of memory for variables!")

    # Check if value is a character in quotes
    if value.startswith("'") and value.endswith("'") and len(value) == 3:
        ascii_value = ord(value[1])  # Extract ASCII value of the character
    else:
        ascii_value = int(value)  # Treat it as a base-10 integer

    # Store the variable in the variables dictionary with its memory address
    variables[name] = f"{next_available_address:04X}"
    machine_code = ["01", f"{ascii_value:02X}", "20", f"{next_available_address:04X}"[:2], f"{next_available_address:04X}"[2:]]  # LIA value, STA address
    next_available_address -= 1  # Decrease available memory address
    return machine_code


def process_operand(operand):
    # Check if operand is a character (e.g., 'A')
    if operand.startswith("'") and operand.endswith("'") and len(operand) == 3:
        return f"{ord(operand[1]):02X}"  # Convert char to its ASCII hex value
    else:
        # Assume the operand is a hex value and return it as-is
        return operand


# Updated Assembler function to handle LIA and LIT with ASCII values or variables
def assemble_code(assembly_code):
    global variables, next_available_address
    machine_code = []
    labels = {}  # Store label positions
    unresolved_jumps = []  # Track unresolved jump addresses
    lines = assembly_code.strip().split("\n")
    current_address = 0  # Track the current address for labels

    # First pass: Identify labels, variables, and store their addresses
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith(";"):  # Skip empty lines and comments
            continue

        # Handle variable assignment (e.g., x = 3)
        if '=' in line:
            parts = line.split('=')
            var_name = parts[0].strip()
            var_value = parts[1].strip()
            # Allocate memory for the variable and add LIA/STA instructions to machine code
            machine_code.extend(allocate_variable(var_name, var_value))
            current_address += 5  # LIA and STA both take 5 bytes
            continue
        
        if '+' in line:
            parts = line.split('+')
            var1 = parts[0].strip()  # The first variable (e.g., rect_0)
            var2 = parts[1].strip()  # The second variable (e.g., square_0)

            if var1 in variables and var2 in variables:
                # Generate the LDA, ADD, STA instructions
                machine_code.append("10")  # LDA opcode
                machine_code.append(variables[var1][:2])  # First byte of rect_0 address
                machine_code.append(variables[var1][2:])  # Second byte of rect_0 address
                current_address += 3

                machine_code.append("30")  # ADD opcode
                machine_code.append(variables[var2][:2])  # First byte of square_0 address
                machine_code.append(variables[var2][2:])  # Second byte of square_0 address
                current_address += 3

                machine_code.append("20")  # STA opcode
                machine_code.append(variables[var1][:2])  # First byte of rect_0 address
                machine_code.append(variables[var1][2:])  # Second byte of rect_0 address
                current_address += 3
            else:
                raise Exception(f"Undefined variable(s): {var1}, {var2}")
            continue


        if '-' in line:
            parts = line.split('-')
            var1 = parts[0].strip()  # The first variable (e.g., rect_0)
            var2 = parts[1].strip()  # The second variable (e.g., square_0)

            if var1 in variables and var2 in variables:
                # Generate the LDA, ADD, STA instructions
                machine_code.append("10")  # LDA opcode
                machine_code.append(variables[var1][:2])  # First byte of rect_0 address
                machine_code.append(variables[var1][2:])  # Second byte of rect_0 address
                current_address += 3

                machine_code.append("31")  # SUB opcode
                machine_code.append(variables[var2][:2])  # First byte of square_0 address
                machine_code.append(variables[var2][2:])  # Second byte of square_0 address
                current_address += 3

                machine_code.append("20")  # STA opcode
                machine_code.append(variables[var1][:2])  # First byte of rect_0 address
                machine_code.append(variables[var1][2:])  # Second byte of rect_0 address
                current_address += 3
            else:
                raise Exception(f"Undefined variable(s): {var1}, {var2}")
            continue


        # Check if the line is a label
        if line.endswith(":"):
            label = line[:-1]
            labels[label] = f"{current_address:04X}"  # Store the label address
            continue

        # Detect PRINT statement
        if line.startswith("PRINT"):
            # Extract the string within quotes
            start_index = line.find('"') + 1
            end_index = line.rfind('"')
            if start_index != -1 and end_index != -1:
                string_to_print = line[start_index:end_index]  # Keep original case for string
                # Convert the string to LIT instructions
                lit_instructions = convert_string_to_lit(string_to_print)
                machine_code.extend(lit_instructions)  # Add LIT instructions to machine code
                current_address += len(lit_instructions)  # Each LIT instruction is 2 bytes
            else:
                raise Exception(f"Invalid PRINT syntax: {line}")
            continue

        # Convert line to uppercase (for opcodes, labels, etc.)
        line = line.upper()
        
        parts = line.split()
        instruction = parts[0]

        # Check if the instruction is valid
        if instruction in opcodes:
            opcode = opcodes[instruction]
            machine_code.append(opcode)
            current_address += 1  # Each opcode is 1 byte
            
            # Handle immediate and memory address operands
            if len(parts) == 2:
                operand = parts[1]

                # Process operand for LIA and LIT (handle ASCII, variable, or integer)
                if instruction in ['LIA', 'LIB', 'LIT',]:
                    processed_operand = process_operand(operand)
                    machine_code.append(processed_operand)
                    current_address += 1
                # Handle variable reference (e.g., LDA x)
                elif operand in variables:
                    address = variables[operand]
                    machine_code.append(address[:2])  # First byte of the address
                    machine_code.append(address[2:])  # Second byte of the address
                    current_address += 2

                # Handle jump commands (JPC, JMP, etc.)
                elif instruction.startswith('J'):
                    # Handle labels for jumps

                    if operand in labels:
                        address = labels[operand]
                        machine_code.append(address[:2])  # First byte of label address
                        machine_code.append(address[2:])  # Second byte of label address
                    else:
                        # If label is not yet defined, record its position for resolution later
                        unresolved_jumps.append((len(machine_code), operand))
                        machine_code.append('00')  # Placeholder bytes
                        machine_code.append('00')
                    current_address += 2

                else:  # Memory address
                    if len(operand) == 4:
                        machine_code.append(operand[:2])  # First byte
                        machine_code.append(operand[2:])  # Second byte
                        current_address += 2
                    else:
                        raise Exception(f"Memory address must be 4 hex digits: {operand}")
            elif len(parts) == 1 and instruction in ['NOP', 'RTR', 'RTL','STI','LDI','RET','JPI','UPD', 'NOT',]:
                continue  # These instructions are single-byte opcodes
            else:
                raise Exception(f"Invalid syntax: {line}")
        else:
            raise Exception(f"Unknown instruction: {instruction}")

    # Second pass: Resolve unresolved jumps
    for pos, label in unresolved_jumps:
        if label in labels:
            address = labels[label]
            machine_code[pos] = address[:2]  # First byte of label address (high byte)
            machine_code[pos + 1] = address[2:]  # Second byte of label address (low byte)
            
        else:
            raise Exception(f"Undefined label: {label}")
    variables.clear()
    next_available_address = 0xFFFF        
    return machine_code  # Important! Return the generated machine code
    

# Function to compile the code
def compile_code():
    assembly_code = text_editor.get("1.0", tk.END)
    try:
        machine_code = assemble_code(assembly_code)
        if machine_code:
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, " ".join(machine_code))  # Display machine code in text area
    except Exception as e:
        messagebox.showerror("Compilation Error", str(e))  # Show error message




# Function to load a file
def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Assembly files", "*.asm"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "r") as file:
            text_editor.delete("1.0", tk.END)
            text_editor.insert(tk.END, file.read())

# Function to save the file
def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".asm", filetypes=[("Assembly files", "*.asm"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(text_editor.get("1.0", tk.END))

# Create the main window
root = tk.Tk()
root.title("Assembly Text Editor & Assembler")

# Create the text editor
text_editor = tk.Text(root, height=5, width=80)
text_editor.pack(padx=10, pady=10)

# Create the output display for machine code
output_text = tk.Text(root, height=40, width=60, bg="lightgray")
output_text.pack(padx=10, pady=10)

# Create the button frame
button_frame = tk.Frame(root)
button_frame.pack()

# Load, Save, and Compile buttons
load_button = tk.Button(button_frame, text="Load", command=load_file)
save_button = tk.Button(button_frame, text="Save", command=save_file)
compile_button = tk.Button(button_frame, text="Compile", command=compile_code)

load_button.grid(row=0, column=0, padx=5, pady=5)
save_button.grid(row=0, column=1, padx=5, pady=5)
compile_button.grid(row=0, column=2, padx=5, pady=5)

# Start the GUI loop
root.mainloop()
