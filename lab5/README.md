In this lab we are going to get an old block from the BitCoin block chain and demonstrate how any changes would be caught by the BitCoin network.

Requirements:

    Connect to a peer in the P2P BitCoin network and get the block number that corresponds to your SU ID number (your number modulo 10,000).
    Display the transactions in the block. [Extra Credit]
    Have your program manipulate one of the transactions in the block to change its output account, then fix up the block to correctly represent this modified data (fix the merkle-tree hashes, etc.). [Extra Credit]
    Then show with a program-generated report how the hash of the block has changed and the ways in which this block would be rejected by peers in the network. [Extra Credit]
    Program written in Python 3 with no use of publicly available BitCoin libraries (except makeseeds as shown below).
    Use TCP/IP to communicate with a full node in the network.
    Submit the program in the usual way on cs1, all in one file, lab5.py.

Start by reading about blockchains in general, the original paper
Links to an external site., and the developer documentation

Links to an external site.. Other resources:

    https://bitcoin.org 

Links to an external site.
https://developer.bitcoin.org/devguide/p2p_network.html
Links to an external site.
wiki
Links to an external site.
https://github.com/bitcoin/bips

    Links to an external site.

Getting Connected

To get a list of bitcoin nodes, use makeseeds
Links to an external site.. This part won't work on cs2, so do it locally. You may need to install dnspython for this to work (pip3 install dnspython or pip install dnspython) and also download asmap.py

Links to an external site.. Follow their directions at the bottom of their page:

curl https://bitcoin.sipa.be/seeds.txt.gz | gzip -dc > seeds_main.txt
curl https://bitcoin.sipa.be/asmap-filled.dat > asmap-filled.dat
python3 makeseeds.py -a asmap-filled.dat -s seeds_main.txt > nodes_main.txt

[NOTE: On Windows, the command is usually python and on a Mac python3.  The makeseeds process can take a few minutes.]

Pick nodes from nodes_main.txt that are not onion nodes
Links to an external site. and just choose one at random that is currently working. You may have to try several before you get a working node. You can leave the host you are using hard-coded in your submitted program.
