import asyncio
import csv
import time
from bleak import BleakScanner
import matplotlib.pyplot as plt

# Function to discover and handle Tilt Hydrometer data using advertisement data
def discover_and_handle_tilt():
    print("Scanning for Tilt Hydrometer...")
    data = []
    filename = "tilt_data.csv"

    def process_advertisement(device, advertisement_data):
            print(f"Device Found: {device.name} ({device.address})")  # Log every device
            manufacturer_data = advertisement_data.manufacturer_data

            # Check if this is a Tilt device by manufacturer data length or specific patterns
            for key, value in manufacturer_data.items():
                hex_data = " ".join(f"{byte:02x}" for byte in value)
                print(f"Manufacturer Data from {device.address}: {hex_data}")  # Debugging
                if value and len(value) >= 4:
                    gravity = int.from_bytes(value[20:22]) / 1000.0
                    temperature_f = int.from_bytes(value[18:20])
                    temperature_c = (temperature_f - 32) * 5.0 / 9.0  # Convert to Celsius

                    # Convert gravity to Plato
                    plato = (259 - (259 / gravity)) - 0.77 if gravity > 0 else 0 #Eichen um 0.77

                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] Plato: {plato:.2f}, Temperature: {temperature_c:.2f} C, Temperature: {temperature_f:.2f} F")

                    # Append data to CSV and memory
                    with open(filename, "a", newline="") as csvfile:
                        csv_writer = csv.writer(csvfile)
                        csv_writer.writerow([timestamp, plato, temperature_c])
                        data.append((timestamp, plato, temperature_c))

    async def scan_and_process():
        # Write headers to CSV
        with open(filename, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Time", "Plato", "Temperature (C)"])

        scanner = BleakScanner(detection_callback=process_advertisement)
        print("Listening for advertisement data. Press Ctrl+C to stop.")
        try:
            await scanner.start()
            while True:
                await asyncio.sleep(5)  # Adjust listening duration as needed
        except KeyboardInterrupt:
            print("Stopping scan.")
        finally:
            await scanner.stop()
            plot_data(data)

    asyncio.run(scan_and_process())

# Function to plot the data
def plot_data(data):
    if not data:
        print("No data collected to plot.")
        return

    timestamps = [d[0] for d in data]
    plato_values = [d[1] for d in data]
    temperature_values = [d[2] for d in data]

    plt.figure(figsize=(10, 5))

    # Plot Plato
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, plato_values, label="Plato", marker="o")
    plt.xlabel("Time")
    plt.ylabel("Plato")
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()

    # Plot Temperature
    plt.subplot(2, 1, 2)
    plt.plot(timestamps, temperature_values, label="Temperature (C)", marker="o", color="orange")
    plt.xlabel("Time")
    plt.ylabel("Temperature (C)")
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        discover_and_handle_tilt()
    except Exception as e:
        print(f"Error: {e}")

