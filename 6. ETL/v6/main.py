from Pipeline.Logger import *
from Pipeline.InstagramAPI import *
from Pipeline.GptAPI import *
from Pipeline.GeoCoding import *
from Pipeline.Mysql import *
from Pipeline.Alert import *

if __name__ == "__main__":
    InstagramAPI.play()
    GptAPI.play(download=True)
    GeoCoding.play()
    Mysql.play(local=True)
    Alert.play(local=True)
    
    