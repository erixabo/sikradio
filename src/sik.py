import serial
import time

def sik_configure(port='/dev/ttyUSB0', baudrate=57600, params=None):
    if params is None:
        params = {"S2": 57}  # Alapértelmezett NetID

    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Kapcsolódva: {port} @ {baudrate} baud\n")

        # AT módba lépés
        time.sleep(1.2)
        ser.reset_input_buffer()
        ser.write(b'+++')
        time.sleep(3.2)
        at_response = ser.read_all().decode(errors="ignore").strip()
        print("[AT mód] válasz:", at_response)

        if "OK" not in at_response:
            print("⚠️ Nem sikerült AT módba lépni.")
            ser.close()
            return

        # Paraméterek beállítása
        # Paraméterek beállítása
        for key, value in params.items():
            at_command = f'ATS{key}={value}\r\n'
            print(f"[Beállítás] {at_command.strip()}")
            ser.write(at_command.encode())
            time.sleep(0.2)

            # Válasz kiolvasása, amíg \r\n vagy OK nem jön
            full_response = b""
            start_time = time.time()
            while True:
                if ser.in_waiting:
                    full_response += ser.read(ser.in_waiting)
                    if b'\r\n' in full_response:
                        break
                if time.time() - start_time > 2:  # 2 másodperc timeout
                    break
                time.sleep(0.05)

            resp = full_response.decode(errors="ignore").strip()
            print("↪︎ Válasz:", resp)

        # EEPROM mentés
        print("\n[EEPROM mentés] AT&W")
        ser.write(b'AT&W\r\n')
        time.sleep(0.2)
        print("↪︎ Válasz:", ser.read_until(b'\r\n').decode().strip())

        # Újraindítás
        print("[Újraindítás] ATZ")
        ser.write(b'ATZ\r\n')
        time.sleep(0.5)
        print("✅ Kész.")

        ser.close()

    except serial.SerialException as e:
        print("❌ Hiba a soros kapcsolatban:", e)

if __name__ == "__main__":
    sik_configure(
        port='/dev/ttyUSB0',
        baudrate=57600,
        params={
            
	    #"0": 26		#S0:FORMAT=26         # eztet nem basztassuk, mert kamu a regiszter
	    "1": 57,		#S1:SERIAL_SPEED=57
	    "2": 32,		#S2:AIR_SPEED=32
	    "3": 77,		#S3:NETID=77
	    "4": 20,		#S4:TXPOWER=20
	    "5": 0,		#S5:ECC=0
	    "6": 0,		#S6:MAVLINK=0
	    "7": 0,		#S7:OPPRESEND=0
	    "8": 433050,	#S8:MIN_FREQ=433050
	    "9": 434780,	#S9:MAX_FREQ=434780
	    "10": 8,		#S10:NUM_CHANNELS=8
	    "11": 100,		#S11:DUTY_CYCLE=100
	    "12": 0,		#S12:LBT_RSSI=0
	    "13": 0,		#S13:MANCHESTER=0
	    "14": 0,		#S14:RTSCTS=0
	    "15": 131		#S15:MAX_WINDOW=131

        }
    )
