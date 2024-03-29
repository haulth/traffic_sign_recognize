from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.core.files.storage import FileSystemStorage
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import io
import random
from keras.models import load_model
from PIL import Image
import os
import sys
import json


os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


def uploadFile(request):
    context = {}
    if request.method == 'POST':
        uploaded_file = request.FILES['image']
        fs = FileSystemStorage()
        name = fs.save(uploaded_file.name, uploaded_file)
        context['url'] = fs.url(name)
    return context


def imreadx(url):
    img = io.imread(url)
    outimg = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return outimg


def imshowx(img, title='B2DL'):
    fig_size = plt.rcParams["figure.figsize"]
    fig_size[0] = 12
    fig_size[1] = 4
    plt.rcParams["figure.figsize"] = fig_size

    plt.axis('off')
    plt.title(title)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.show()


def imshowgrayx(img, title='BD2L'):
    plt.axis('off')
    plt.title(title)
    plt.imshow(img, cmap=plt.get_cmap('gray'))
    plt.show()


def cropAndDetectTrafficSign(context):

    try:
        currentPythonFilePath = os.getcwd()
        
        #sử dụng .replace('\\','/') để thay đổi dấu / đg dẫn.
        modelUrl = currentPythonFilePath+'/static/model/model_36class_20epochs.h5'.replace('\\','/')
        
        saveDetectImageUrl = currentPythonFilePath+'/static/image/'.replace('\\','/')
        url = currentPythonFilePath + context['url']
        

        imageType = url.split('.')[1]
       
        img = cv2.imread(url)
       
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_r1 = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
        mask_r2 = cv2.inRange(hsv, (160, 100, 100), (180, 255, 255))
        mask_r = cv2.bitwise_or(mask_r1, mask_r2)
        target = cv2.bitwise_and(img, img, mask=mask_r)
        gblur = cv2.GaussianBlur(mask_r, (9, 9), 0)
        edge_img = cv2.Canny(gblur, 30, 150)
      
        cv2.imwrite(saveDetectImageUrl + 'original.'+imageType, img)
        cv2.imwrite(saveDetectImageUrl + 'markrange1.'+imageType, mask_r1)
        cv2.imwrite(saveDetectImageUrl + 'markrange2.'+imageType, mask_r2)
        cv2.imwrite(saveDetectImageUrl + 'maskforredregion.'+imageType, mask_r)
        cv2.imwrite(saveDetectImageUrl + 'maskforredrigon.'+imageType, target)
        cv2.imwrite(saveDetectImageUrl + 'edgemap.'+imageType, edge_img)

        img2 = img.copy()
        # delete the imt
        cnts, hierarchy = cv2.findContours(
            edge_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img2, cnts, -1, (0, 255, 0), 2)

        cv2.imwrite(saveDetectImageUrl +
                    'contournorestriction.'+imageType, img2)

        img2 = img.copy()
        try:
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if(area < 1000):
                    continue
                ellipse = cv2.fitEllipse(cnt)
                cv2.ellipse(img2, ellipse, (0, 255, 0), 2)
                x, y, w, h = cv2.boundingRect(cnt)
                a, b, c, d = x, y, w, h
                cv2.rectangle(img2, (x, y), (x+w, y+h), (0, 255, 0), 3)

            cv2.imwrite(saveDetectImageUrl +
                        'contourrestrictedforlargeregion.'+imageType, img2)
            #cần sửa crop = img2[b:b+d, a:a+c] thành crop = img2[y:y+h, x:x+w]
            crop = img2[y:y+h, x:x+w]

            cv2.imwrite(saveDetectImageUrl + 'cropimage.'+imageType, crop)

            model = load_model(modelUrl)
            data = []
            image_from_array = Image.fromarray(crop, mode='RGB')
         
            crop = image_from_array.resize((30, 30))

            data.append(np.array(crop))

            X_test = np.array(data)

            X_test = X_test.astype('float32')/255

            prediction1 = model.predict(X_test)
            
            #lấy giá trị lớn nhất sau khi dự đoán
            prediction = np.argmax(prediction1)
            
            return prediction
        except:
            print("cannot border box")
            os.remove(saveDetectImageUrl + 'cropimage.'+imageType)
            cv2.imwrite(saveDetectImageUrl + 'cropimage.'+imageType, img)
            model = load_model(modelUrl)
            data = []
            image_from_array = Image.fromarray(img, 'RGB')
            img = image_from_array.resize((30, 30))
            data.append(np.array(img))
            X_test = np.array(data)
            X_test = X_test.astype('float32')/255

            prediction1 = model.predict(X_test)
            #lấy giá trị lớn nhất sau khi dự đoán
            prediction = np.argmax(prediction1)
            
            return prediction
    except:
        print("Bug when model predict")
        return [10000]
    
#bỏ thông số prediction[0] thành prediction
def detectTrafficSign(request):
    context = uploadFile(request)
    prediction = cropAndDetectTrafficSign(context)
    strin= str(prediction)
    context['traffictrainid'] = prediction
    path = os.getcwd()
    # with open(path +"/static/json/trafficinfomation.json", "r", encoding="utf-8") as f:
    #     dict_translate = json.load(f)
    # for item in dict_translate:
    #    if item['trafficid'] == '-'+strin+'-':
    #        print(item['name'])
    #        print(item['description'])
        
    return context
