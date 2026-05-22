FROM public.ecr.aws/lambda/python:3.12

COPY src/deployment/predict_price.py src/model_engineering/train_models.py ${LAMBDA_TASK_ROOT}/

COPY models/v1/model_luxury.joblib models/v1/model_normal.joblib ${LAMBDA_TASK_ROOT}/models/

RUN pip install pandas xgboost scikit-learn joblib category_encoders --no-cache-dir

CMD [ "predict_price.lambda_handler" ]