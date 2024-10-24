"""
CPSC 5520, Seattle University
This is a client that connects to a Group Coordinator Daemon (GCD), which returns a list of group members.
The client then sends a message to each group member, engages in a Bully election process, and prints the election result.
:Author: Zhou Liu 
:Version: 01
:@lab2.py
:Date: 10/15/2024
"""
import pickle
import socket
import sys
import threading
import time
import socketserver

BUF_SIZE = 1024  # Buffer size for receiving data
TIMEOUT = 5  # Timeout in seconds for socket operations

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """Request handler for incoming messages."""
    
    def handle(self):
        try:
            raw_message = self.request.recv(BUF_SIZE)
            message = pickle.loads(raw_message)
            messageType, sender_id = message
            print(f"Received message {messageType} from {sender_id}")
            self.server.client.report_message((messageType, sender_id))
        except Exception as e:
            print(f"Error: {e}")


class Client:
    def __init__(self, ID, gcdHost, gcdPort):
        """
        Initialize a Bully Client instance.
        :param processID: Tuple representing (daysToBirthday, studentID).
        :param gcdHost: GCD server host.
        :param gcdPort: GCD server port.
        """
        self.processID = ID
        self.gcdHost = gcdHost
        self.gcdPort = gcdPort
        self.leader = None
        self.member = {}
        self.running = True
        self.listenerPort = None
        self.messages = []  # Queue for thread-safe messages
        self.message_sync = threading.Event()  # Event to synchronize threads
        self.message_flag = threading.Event()  # Flag to signal new messages

        # Create a TCP socket for sending messages
        self.sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sender_socket.settimeout(TIMEOUT)

    def report_message(self, message):
        """Put a message on the message queue in a thread-safe manner."""
        self.message_sync.wait()  # Respect harvester's lock
        self.messages.append(message)  # Thread-safe add
        self.message_flag.set()  # Notify the main thread to look

    def harvest_messages(self):
        """Get any unprocessed messages and reset the message queue."""
        self.message_sync.clear()  # Lock threads out
        messages = self.messages
        self.messages = []
        self.message_flag.clear()  # Clear the flag
        self.message_sync.set()  # Let threads back in
        return messages

    def get_members(self):
        """Register with the GCD server and get the current group members."""
        # Get the localhost IP address
        localhostIP = socket.gethostbyname('localhost')

        # Bind the listener socket to an available port
        self.listenerPort = self.getListernerPort(localhostIP)
        print(f"Listening on port {self.listenerPort}")

        # Create the registration message
        registration_message = ('BEGIN', (self.processID, (localhostIP, self.listenerPort)))

        # Connect to the GCD and send registration
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gcd_socket:
                gcd_socket.connect((self.gcdHost, self.gcdPort))
                gcd_socket.sendall(pickle.dumps(registration_message))
                response = pickle.loads(gcd_socket.recv(BUF_SIZE))

            # Update group information
            self.member = response
            print(f"Registered with GCD. Current group: {self.member}")
        except Exception as e:
            print(f"Fail to connect to GCD server: {e}")

    def getListernerPort(self, host):
        """Find an available port for the TCP server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, 0))
            return s.getsockname()[1]

    def parse_message(self, messageType, sender_id):
        """Handle incoming messages from other clients."""
        if messageType == "ELECTION":
            print(f"Received ELECTION message from {sender_id}.")
            if self.processID[1] > sender_id[1]:
                self.send_message(sender_id, "OK")
                self.start_election()

        elif messageType == "OK":
            print(f"Received OK message from {sender_id}. Election in progress.")

        elif messageType == "COORDINATOR":
            print(f"Received COORDINATOR message from {sender_id}. Setting {sender_id} as leader.")
            self.leader = sender_id

    def send_message(self, receiverID, messageType):
        """Send a message to a specific group member."""
        if receiverID not in self.member:
            print(f"Target {receiverID} not in the member list.")
            return
        receiverAddress = self.member[receiverID]
        message = (messageType, self.processID)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                print(f"Sending {messageType} to {receiverID} at {receiverAddress}.")
                s.connect(receiverAddress)
                s.sendall(pickle.dumps(message))
                print(f"Message {messageType} sent to {receiverID}.")
            except socket.error as e:
                print(f"Failed to send {messageType} to {receiverID}. Error: {e}")

    def start_election(self):
        """Start the Bully Algorithm election."""
        print("Starting election...")
        self.leader = None

        # Send ELECTION message to all higher process IDs
        for pid in self.member:
            if pid[1] > self.processID[1]:
                print(f"Sending ELECTION message to {pid}.")
                self.send_message(pid, "ELECTION")

        # Wait for responses
        time.sleep(TIMEOUT)

        # If no one responded, declare self as the coordinator
        if not self.leader:
            print("No higher ID processes responded. I am the new leader.")
            self.leader = self.processID
            self.announce_leader()

    def announce_leader(self):
        """Announce self as the new leader to all group members."""
        print(f"{self.processID} is announcing self as COORDINATOR.")
        for pid in self.member:
            if pid != self.processID:
                self.send_message(pid, "COORDINATOR")

    def run(self):
        """Run the client: register with GCD and start listening for messages."""
        self.get_members()

        # Start the server thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

        # Initial election to choose a leader
        self.start_election()

        # Keep the client running and processing messages
        try:
            while self.running:
                if self.message_flag.is_set():
                    messages = self.harvest_messages()
                    for messageType, sender_id in messages:
                        self.parse_message(messageType, sender_id)
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False

    def start_server(self):
        """Start a threaded TCP server to listen for incoming connections."""
        localhostIP = socket.gethostbyname('localhost')
        server = socketserver.ThreadingTCPServer((localhostIP, self.listenerPort), ThreadedTCPRequestHandler)
        server.client = self  # Share client instance with the request handler
        server.serve_forever()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python lab2.py daysToBirthday studentID GCDPORT")
        exit(1)

    # Parse command line arguments
    daysToBirthday = int(sys.argv[1])
    studentID = int(sys.argv[2])
    gcdPort = int(sys.argv[3])
    gcdHost = 'localhost'

    # Create process ID
    processID = (daysToBirthday, studentID)

    # Create and run the Bully client
    client = Client(processID, gcdHost, gcdPort)
    client.run()