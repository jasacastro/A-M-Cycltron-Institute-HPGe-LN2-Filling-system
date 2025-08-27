# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 14:15:56 2025

@author: Jason
"""

import tkinter as tk
from tkinter import messagebox
import serial
import time
import re
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage


def send_email_alert(subject, body, to_email):
    EMAIL_ADDRESS = "castrojason111@gmail.com"
    EMAIL_PASSWORD = "gjre zqqn jmsg bxrv"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Email failed: {e}")
        
        
# Class to make the individual Dewar Panels
class DewarPanel:
    def __init__(self, parent, dewar_id, send_command_callback):
        self.dewar_id = dewar_id
        self.send_command = send_command_callback
        self.frame = tk.Frame(parent, bd=3, relief='ridge', padx=10, pady=10)

        tk.Label(self.frame, text=f"Dewar #{dewar_id}", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        self.start_button = tk.Button(self.frame, text="Start Filling", width=20,
                                      command=lambda: self.handle_start())
        self.start_button.pack(pady=2)

        self.stop_button = tk.Button(self.frame, text="Stop Filling", width=20,
                                     command=self.handle_stop)
        self.stop_button.pack(pady=2)

        self.auto_fill = tk.BooleanVar(value=True)
        self.auto_check = tk.Checkbutton(self.frame, text="Auto-Stop Enabled", variable=self.auto_fill,
                                         command=self.toggle_auto)
        self.auto_check.pack(pady=5)
        
        self.email_alerts = tk.BooleanVar(value=True)  # Default to ON
        self.email_check = tk.Checkbutton(self.frame, text="Email Alerts Enabled", variable=self.email_alerts)
        self.email_check.pack(pady=2)

        self.temp_label = tk.Label(self.frame, text="Current Temp: --- °C", fg="green")
        self.temp_label.pack()
        
        self.fill_start_time = None
        self.fill_duration_var = tk.StringVar(value="Fill Duration: ---")
        tk.Label(self.frame, textvariable= self.fill_duration_var, font=("Courier", 8 )).pack()
        
        self.stop_temp_var = tk.StringVar(value="Stop Temp: ---°C")
        tk.Label(self.frame, textvariable=self.stop_temp_var, font=("Courier", 8)).pack()

        self.last_fill_var = tk.StringVar(value="Last Fill: ---")
        tk.Label(self.frame, textvariable=self.last_fill_var, font=("Courier", 8)).pack()

        self.next_fill_var = tk.StringVar(value="Next Fill: ---")
        tk.Label(self.frame, textvariable=self.next_fill_var, font=("Courier", 8)).pack()

        self.countdown_var = tk.StringVar(value="Countdown: ---")
        tk.Label(self.frame, textvariable=self.countdown_var, font=("Courier", 8)).pack()

        self.next_fill_datetime = None
        self.update_countdown()

    def toggle_auto(self):
        if self.auto_fill.get():
            self.send_command(f"AUTO_ON_{self.dewar_id}")
        else:
            self.send_command(f"AUTO_OFF_{self.dewar_id}")
            

    def update_temperature(self, temp):
        self.temp_label.config(text=f"Current Temp: {temp:.2f} °C")

    def mark_fill_time(self):
        now = datetime.now()
        self.last_fill_var.set(f"Last Fill: {now.strftime('%I:%M %p | %x')}")
        self.next_fill_datetime = now + timedelta(hours=4)
        self.next_fill_var.set(f"Next Fill: {self.next_fill_datetime.strftime('%I:%M %p | %x')}")
        
        if self.fill_start_time:
            duration = now - self.fill_start_time
            self.fill_duration_var.set(f"Fill Duration: {str(duration).split('.')[0]}")
            self.stop_temp_var.set(f"Stop Temp: {self.temp_label.cget('text').split(': ')[1]}")
            self.fill_start_time = None
            
        if self.email_alerts.get():  # Only send if enabled
            subject = f"LN2 Fill Completed - Dewar #{self.dewar_id}"
            body = (
                f"The LN2 fill for Dewar #{self.dewar_id} has completed.\n"
                f"Finish Time: {now.strftime('%I:%M %p | %x')}\n"
                f"Fill Duration: {str(duration).split('.')[0]}\n"
                f"Next Fill Recommended After: {self.next_fill_datetime.strftime('%I:%M %p | %x')}"
            )
            to_email = ""  # Replace with your address ***FOR EMAIL FUNCTION TO WORK: WRITE EMAIL INSIDE  the ""
            send_email_alert(subject, body, to_email)
                                    

    def handle_stop(self):
        self.send_command(f"OFF_{self.dewar_id}")
        self.mark_fill_time()

    def handle_start(self):
        self.fill_start_time = datetime.now()
        self.send_command(f"ON_{self.dewar_id}")


    def update_countdown(self):
        if self.next_fill_datetime:
            now = datetime.now()
            remaining = self.next_fill_datetime - now
            if remaining.total_seconds() > 0:
                hrs, rem = divmod(int(remaining.total_seconds()), 3600)
                mins, secs = divmod(rem, 60)
                self.countdown_var.set(f"Countdown: {hrs}h {mins}m {secs}s")
            else:
                self.countdown_var.set("Cooldown complete.")
        self.frame.after(1000, self.update_countdown)
        
 # Class to make the rest of the GUI
class LN2ControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LN2 GUI System Control")
        self.root.geometry("1400x700")

        self.arduino = None

        self.status_label = tk.Label(root, text="Status: Not connected", font=("Helvetica", 10))
        self.status_label.pack(anchor='w', padx=20, pady=(10, 0))

        self.command_label = tk.Label(root, text="", font=("Helvetica", 10), fg="blue")
        self.command_label.pack(anchor='e', padx=20)

        tk.Label(root, text="LN2 Filling System Controls", font=("Helvetica", 22)).pack(pady=15)

        self.top_row = tk.Frame(root)
        self.top_row.pack()

        self.bottom_row = tk.Frame(root)
        self.bottom_row.pack()

        self.dewar_panels = []
        for i in range(1, 5):                                          # Change depending on how many dewars you want 
            target_row = self.top_row if i <= 4 else self.bottom_row   # Cahnge depending on how many dewars you want per row, 6 max per row
            panel = DewarPanel(target_row, i, self.send_command)
            panel.frame.pack(side="left", padx=10, pady=15)
            self.dewar_panels.append(panel)

        try:
            self.arduino = serial.Serial('COM3', 115200, timeout=1)
            time.sleep(2)
            self.status_label.config(text="Status: Connected to COM3")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not open serial port:\n{e}")
            self.status_label.config(text="Status: Connection Failed")
            self.arduino = None

        self.poll_temperature()

    def send_command(self, command):
        if self.arduino and self.arduino.is_open:
            print(f"sending: {command}")
            self.arduino.write(f"{command}\n".encode())
            time.sleep(0.1) # small pause to avoid overloading
            self.command_label.config(text=f"Sent: {command}")
        else:
            messagebox.showwarning("Warning", "Serial port not open")
            

    def poll_temperature(self):
        if self.arduino and self.arduino.in_waiting:
            try:
                line = self.arduino.readline().decode(errors='ignore').strip()
                for i in range(8):
                    if f"AUTO_OFF_{i+1}" in line:
                        self.dewar_panels[i].mark_fill_time()
                    match = re.search(f"Sensor {i+1} Temperature = ([+-]?[0-9]*\.?[0-9]+)", line)
                    if match:
                        temp = float(match.group(1))
                        self.dewar_panels[i].update_temperature(temp)
            except:
                pass
        self.root.after(500, self.poll_temperature)

    def close(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = LN2ControlGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.close(), root.destroy()))
    root.mainloop()