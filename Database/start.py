from lib2to3.pgen2.grammar import opmap_raw
from msilib.schema import AdminExecuteSequence
from re import X
from unicodedata import name
import boto3
import socket
from decimal import Decimal
from pprint import pprint
from boto3.dynamodb.conditions import Key
from random import randrange

def create_user_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb',region_name='us-east-1')

    table = dynamodb.create_table(
        TableName='Users',
        KeySchema=[
            {
                'AttributeName': 'User', # the User value is the socket value of a player
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'Name',
                'KeyType': 'RANGE' # Sort key
            } 
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'User',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'Name',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    print("created table")
    return table

def add_user(user,name,socket_addr,is_admin,dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Users')
    response = table.put_item(
        Item={
            'User': user,
            'Name' : name,
            'info': {
                'points': 0,
                'is_admin' : is_admin
            }
        }
    )
    print("added user")
    return response

def update_points(user, name, point):#pass param is the new password
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Users')
    response = table.update_item(
        Key={
            'User':user,
            'Name':name
        },
        UpdateExpression = "set info.points=:r",
        ExpressionAttributeValues={
            ':r': point
        },
        ReturnValues = "UPDATED_NEW"
    )
    return response

def query_user(user, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
    table = dynamodb.Table('Users')
    response = table.query(
        KeyConditionExpression=Key('User').eq(user)
    )
    results = response['Items']
    for result in results:
        return(result)
    print("finished query")

def delete_user_table(dynamodb=None):
    try:
        if not dynamodb:
            dynamodb = boto3.resource('dynamodb', region_name="us-east-1")

        table = dynamodb.Table('Users')
        print("deleted table")
        table.delete()
    except:
        pass


def main():
    print("Server has started running")
    delete_user_table()
    table = create_user_table()
    server_port = 12000
    #create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #bind the server to the localhost at port server_port
    server_socket.bind(('0.0.0.0',server_port))
    #ready message
    print('Chat server running on port ', server_port)

    #Now the loop that actually listens from clients
    #The same server socket serves all clients here

    board1 = ('0.0.0.0', 11000)
    board2 = ('0.0.0.0', 12000)
    board3 = ('0.0.0.0', 13000)
    board4 = ('0.0.0.0', 14000)
    board5 = ('0.0.0.0', 15000)
    board6 = ('0.0.0.0', 16000)
    wordle_characters = ["l","r","1","2","3"]
    wordle_length = 5
    game_started = False
    number_players = 0
    players = []

    
    while True:
        if not game_started:
            # two types of messages from client:
            # 1) new user joins - just sends his name
            #     example message: user1
            # 2) admin starts game
            #     message: admin start
            cmsg, cadd = server_socket.recvfrom(2048) 
            cmsg = cmsg.decode()
            cmsg = cmsg.split()
            if len(cmsg)==2 and cmsg[0]=="admin" and cmsg[1]=="start":
                game_started = True
                cmsg = "game started"
                server_socket.sendto(cmsg.encode(), cadd)
                wordle = ""
                for i in range(5):
                    x = int(randrange(4))
                    wordle+=wordle_characters[x]
                game_over = False
            else:
                is_admin = True if number_players == 0 else False
                add_user(cadd, cmsg[0], is_admin)
                players+=cadd
                number_players+=1
                cmsg = "player added"
                server_socket.sendto(cmsg.encode(), cadd)
        else:
            #game has started
            #client waits until they receive the message "Your turn"
            # Once client receives this message, they enter their move and it is sent to the server.
            # client then sends ggrgy for example to all clients (g means right character, right place, y means right character, wrong place, r means wrong character)
            # When game ends, the server sends all clients the message: "Game over! x wins"
            while game_started:
                for player in players: #go through each player's turn
                    if not game_started:#if game has ended we can end the for loop and leave this section
                        break
                    else:
                        cmsg = "Your turn"
                        server_socket.sendto(cmsg.encode(), cadd)
                        valid_reply = False
                        while not valid_reply: #keep searching for replies until we get a 5 bit word from the player who's go it is.
                            cmsg, cadd = server_socket.recvfrom(2048)
                            guess = cmsg.decode()
                            if cadd == player and len(guess) == 5:
                                valid_reply = True
                        guess_reply = ""
                        correct_guess = True
                        for i in range(5): # in this loop we derive the wordle reply to a guess
                            if guess[i]==wordle[i]:
                                guess_reply += "g"
                            elif guess[i] in wordle:
                                guess_reply += "y"
                                correct_guess = False
                            else:
                                guess_reply += "r"
                                correct_guess = False
                        if correct_guess: # if correct guess we send a message saying game over to everyone, and end this section
                            game_started = False
                            cmsg = "Correct guess! Game over! Winner is: " + player
                            for x in players:
                                server_socket.sendto(cmsg.encode(), x)
                            break
                        else:
                            for x in players:
                                server_socket.sendto(guess_reply.encode(), x)

                        

                            #to do: update points after a winner - do it when working with Omar

                            

                        
            

    
                        
                            
                        


                    
    

            
            





#extra for tcp socket:

#ready message

#Now the loop that actually listens from clients

        
            
# to add a new device:
#     add player1

# the first player to be added is going to be assigned admin 
#     start player1

# at each go, i receive a message asking if its my go
# i reply "y" if its your go, else "n". if the game has ended ill send game over winner: player1
# message will be: turn player1

# player whos turn it is guesses a go:
# guess LRLR player1









            
            
                


            
        
        
    #     cmsg = x[1] + " added"
    #     connection_socket.send(cmsg.encode())
    # elif x[0] == "getpass":
    #     cmsg = str(query_user(x[1])['info']['password'])
    #     connection_socket.send(cmsg.encode())
    # elif x[0] == "guesspass":
    #     actual_password = str(query_user(x[1])['info']['password'])
    #     if x[2] == actual_password:
    #         cmsg = "Correct!"
    #     else:
    #         cmsg = "Wrong!"
    #     connection_socket.send(cmsg.encode())
    # elif x[0] == "updatepass":
    #     update_password(x[1], x[2], x[3])
    #     cmsg = "updated password!"
    #     connection_socket.send(cmsg.encode())