"""
CPSC 5520, Seattle University
This is a simple client that connects to a Group Coordinator Daemon (GCD), which return a list of group members. 
The client then sends a message to each group member, prints their responses, and exits.
:Author: Zhou Liu
:Version: 01
:Date: 10/03/2024
"""
import sys # Import the sys for command-line argument handling
import socket # Import the socket for network communication
import pickle # Import the pickle for serializing and deserializing objects

# Initialize a buffer size for receiving data
BUF_SIZE = 1024

def get_members(host, port): 
    """Connect to the Group Coordinator Daemon (GCD) and get the list of group members."""
    try:
        # Create a TCP socket and connect to the GCD
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Connect to the specified host and port
            s.connect((host, port)) 
            # Send a 'BEGIN' message to the GCD
            s.sendall(pickle.dumps('BEGIN'))
            # Print the connection initiation message
            print(f"BEGIN ({host}, {port})") 
            # Receive information of the list of members
            data = s.recv(BUF_SIZE)
            # Deserialize the received data back into a object (list of members)
            members = pickle.loads(data)
            # Return the list of group members
            return members 
        
    except Exception as e:
        # Handle any connection errors and exit the program
        print (f"Connection Fail: {e}" )
        sys.exit(1)
    
def send_message(member):
    """Send a 'HELLO' message to a each member and print the response."""
    try:
        # Create a TCP socket and connect to the GCD
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set a timeout of 1.5 seconds for the connection
            s.settimeout(1.5) 
            # Connect to the member's host and port
            s.connect((member['host'], member['port'])) 
            # Send a 'HELLO' message to the member
            s.sendall(pickle.dumps('HELLO'))
            # Print the message about communication with the member
            print(f"HELLO to {member}") 
            # Receive the response from the member
            answer = s.recv(BUF_SIZE)
            # Deserialize the received response
            message = pickle.loads(answer)
            # Print the message received from the member
            print(message)

    except socket.timeout:
        # Handle timeout exceptions for the connection attempt
        print(f"Connection timed out with {member}.")
    
    except Exception as e:
         # Handle any other connection errors
        print(f"Connection Fail: {e}")

if __name__ == '__main__':
    # Check that the correct number of command-line arguments is provided
    if len(sys.argv) != 3:
        # Print usage instructions
        print("Usage: python3 lab1.py <GCD_HOST> <GCD_PORAT>")
        # Exit the program if the arguments are incorrect
        sys.exit(1)
    # Get the host and port from command-line arguments
    host, port = sys.argv[1], int(sys.argv[2])
    # Get the list of group members from the GCD
    members = get_members(host, port)
    # Send a message to each member in the list
    for member in members:
        send_message(member)
            
