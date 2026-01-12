from Pipeline.Logger import *
from Pipeline.InstagramAPI import *
from Pipeline.GptAPI import *
from Pipeline.GeoCoding import *
from Pipeline.Mysql import *
from Pipeline.Alert import *

if __name__ == "__main__":
    InstagramAPI.play({
        "main": "팝업스토어",
        "sub": {
            "두쫀쿠팝업": "두쫀쿠",
            "두바이쫀득쿠키": "두쫀쿠"
        }
    })
    GptAPI.play(download=True)
    GeoCoding.play()
    # Mysql.play(local=True)
    # Alert.play(local=True)