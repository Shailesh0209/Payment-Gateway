@app.route('/createOnlinePayment', methods=['POST'])
def createOnlinePayment():
 
    razorpay_key_id = "rzp_test_qWajLx8r8ZHzDv"
    razorpay_key_secret = "ZAlQUhomSbLlSngmS2hAATVF"

    razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret)) 

    try:
        connection.begin()

        amount = request.args.get('amount', type=float)
        order_receipt = request.args.get('user_id', type=str)

        if not amount or not order_receipt:
            response_logger.info("createOnlinePayment : order_receipt: %s error : Mandatory field is missing",{order_receipt}, exc_info=True)
            return jsonify({ "Message":"Mandatory field is missing","result_code":1})
        else:
            cursor = connection.cursor()
        
            currency = "INR"
            payment_data = {
                "amount": amount,
                "currency": currency,
                'receipt': order_receipt,
                "payment_capture": 1  
            }
            
            payment_response = razorpay_client.order.create(data=payment_data)
            payment_id = payment_response['id']
            status = payment_response['status']
        
            if status.lower() == 'created':
                insQuery = "INSERT INTO `GENVERSE_PAYMENT` ( `Payment_Id`, `User_Id`, `Amount`, `Payment_Status`) VALUES (%s,%s,%s,%s)"
                cursor.execute(insQuery,(payment_id,order_receipt,amount,status),)
                connection.commit()
                cursor.close()
                print(payment_response)
                response_logger.info("createOnlinePayment : order_receipt: %s : message : Successfully created online payment id",{order_receipt}, exc_info=True)
                return jsonify({" Message" : "Successfully created online payment id","result_code": 0}),200
                
            else:
                response_logger.info("createOnlinePayment : order_receipt: %s : message : Payment ID is not created",{order_receipt},  exc_info=True)
                return jsonify({"Message":"Payment ID is not created",    "result_code":1}),200
        
    except pymysql.Error as err:
                connection.rollback()
                response_logger.info("createOnlinePayment : order_receipt: %s : message : An error occurred while inserting details in DB : error : %s",{order_receipt,str(e)},  exc_info=True)
                return jsonify({"Message": f"An error occurred while inserting details in DB"," error": {str(err)}, "result_code": 1})
    except Exception as e:
            connection.rollback()
            response_logger.info("createOnlinePayment : order_receipt: %s : message : An error occurred while inserting details in DB : error : %s",{order_receipt,str(e)},  exc_info=True)
            return jsonify({"Message": f"An error occurred while inserting details in DB"," error": {str(err)}, "result_code": 1})


@app.route('/paymentWebhook', methods=['POST'])
def payment_webhook():
    try:
        payment_response = request.get_json()
        if not payment_response:
            response_logger.info("paymentWebhook : payment_webhook : error : payment input is empty", exc_info=True)
            return jsonify({ "Message":"payment input is empty","result_code":1})
        else: 
            payment_id = payment_response["payload"]["payment"]["entity"]["order_id"]
            print(payment_id,"payment_id")
            useridStr = payment_response["payload"]["payment"]["entity"]["description"]
            userid = int(useridStr)
            order_success_id = payment_response["payload"]["payment"]["entity"]["id"]
            payment_status = payment_response["payload"]["payment"]["entity"]["status"]
    
            cursor = connection.cursor()

            if payment_status.lower() == "failed":
                failedStatus = "UPDATE `GENVERSE_PAYMENT` SET `Payment_Status` = %s WHERE `Payment_Id` = %s AND `User_Id` = %s"
                cursor.execute(failedStatus, (payment_status,payment_id, userid))
                logging.info(f"Updated User_Id {userid}")
            elif payment_status.lower() == "captured":
                successStatus = "UPDATE `GENVERSE_PAYMENT` SET `Order_Success_id`=%s, `Payment_Status` = %s WHERE `Payment_Id` = %s AND `User_Id` = %s"
                cursor.execute(successStatus, (order_success_id,payment_status,payment_id, userid))
            
            connection.commit()
            cursor.close()
            response_logger.info("paymentWebhook : payment_webhook : userid: %s message : payment details updated successfully",{userid}, exc_info=True)
            return jsonify({"Message": "Payment details updated successfully", "result_code": 0})

    except pymysql.Error as err:
        connection.rollback()
        response_logger.info("paymentWebhook : payment_webhook : message: An error occurred while updating the payment details : error : %s" ,{str(e)},  exc_info=True)
        return jsonify({"Message": f"An error occured while updating the payment details"," error": {str(err)}, "result_code": 1})
    
    except Exception as e:
        connection.rollback()
        response_logger.info("paymentWebhook : payment_webhook : message : An error occurred while updating the payment details : error : %s",{str(e)},  exc_info=True)
        return jsonify({"Message": f"An error occured while updating the payment details"," error": {(e)}, "result_code": 1})