import serial
import json
import time
import argparse
import sys

READ_COMMANDS = [f'ATI{i}' for i in range(8)]
WRITE_COMMANDS = [f'S{x}' for x in range(16)]  # S0–S15

def enter_command_mode(ser):
    print("AT módba lépés kísérlete...")
    ser.flushInput()
    time.sleep(1.1)
    ser.write(b'+++')
    time.sleep(1.1)
    response = ser.readlines()
    decoded = [line.decode(errors='ignore').strip() for line in response]
    print(f"AT mód válasz: {decoded}")
    return any('OK' in line for line in decoded)

def send_at_command(ser, command):
    ser.write((command + '\r\n').encode('ascii'))
    time.sleep(0.2)
    response = ser.readlines()
    return [line.decode('ascii', errors='ignore').strip() for line in response if line.strip()]

def read_radio(ser, outfile):
    result = {}
    if not enter_command_mode(ser):
        print("Nem sikerült AT módba lépni!")
        return

    for cmd in READ_COMMANDS:
        print(f"Küldés: {cmd}")
        response = send_at_command(ser, cmd)
        result[cmd] = response
        print(f"Válasz: {response}")
        time.sleep(0.2)

    print("\nMentés JSON fájlba...")
    with open(outfile, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Mentve ide: {outfile}")

def write_radio(ser, infile):
    print(f"Beállítások visszatöltése a(z) {infile} fájlból...")
    try:
        with open(infile, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Hiba a JSON fájl beolvasásakor: {e}")
        return

    if not enter_command_mode(ser):
        print("Nem sikerült AT módba lépni!")
        return

    ati5_lines = config.get("ATI5", [])[2:]
    ats_commands = []

    for line in ati5_lines:
        if line.startswith('S') and ':' in line and '=' in line:
            try:
                # pl: S1:SERIAL_SPEED=57
                s_label, rest = line.split(':', 1)
                _, value = rest.split('=', 1)
                s_index = int(s_label[1:])  # S1 → 1
                cmd = f"ATS{s_index}={value.strip()}"
                ats_commands.append((s_index, cmd))
            except Exception as e:
                print(f"Hibás sor az ATI5-ben: {line} ({e})")


    ats_commands.sort()  # sorrendbe rakjuk S0-S15

    for index, cmd in ats_commands:
        print(f">>> Írás: {cmd}")
        response = send_at_command(ser, cmd)
        print(f"    Válasz: {response}")
        time.sleep(0.4)

    # EEPROM mentés + újraindítás
    print("\nMentés EEPROM-ba: AT&W")
    print("Újraindítás: ATZ")
    response = send_at_command(ser, 'AT&W')
    print(f"AT&W → {response}")
    time.sleep(0.4)
    response = send_at_command(ser, 'ATZ')
    print(f"ATZ → {response}")


def main():
    parser = argparse.ArgumentParser(description="SiK rádió olvasó/író eszköz")
    parser.add_argument("port", help="Soros port pl. /dev/ttyUSB0")
    parser.add_argument("file", help="JSON fájlnév pl. sikradio.json")
    parser.add_argument("-r", "--read", action="store_true", help="Rádió olvasása JSON-ba")
    parser.add_argument("-w", "--write", action="store_true", help="JSON fájlból visszaírás rádióba")
    parser.add_argument("--baud", type=int, default=57600, help="Baud rate (alapértelmezett: 57600)")

    args = parser.parse_args()

    if not args.read and not args.write:
        print("Hiba: meg kell adni legalább az -r vagy -w kapcsolót.")
        sys.exit(1)

    try:
        with serial.Serial(args.port, args.baud, timeout=2) as ser:
            print(f"Kapcsolódva: {args.port} ({args.baud} baud)")
            if args.read:
                read_radio(ser, args.file)
            if args.write:
                write_radio(ser, args.file)
            send_at_command(ser, "ATZ")     
            print("Újraindítás...")
    except serial.SerialException as e:
        print(f"Soros port hiba: {e}")

if __name__ == "__main__":
    main()
