## MastNet 
Code repository for [A Masked Autoencoder Network for Spatiotemporal Prediction](www.baidu.com).
### About
Spatiotemporal prediction is a hot topic receiving growing interests because of its wide applications. Recently, many works have built predictive structures upon RNN and CNN to learn temporal dependencies and spatial correlations simultaneously. However, due to the increasingly deep-in-time networks, these models easily suffer from the vanishing gradient problem and fail to capture the long-term dependencies effectively. To make longer predictions, this paper introduces a novel predictive network named MastNet based on Transformer. MastNet presents a hierarchical architecture with four cascade stages, which can aggregate multi-level features into predictions. MastNet employs two successive spatiotemporal transformer blocks enabling our model to capture the long-term and short-term spatiotemporal dependencies automatically. Then, MastNet adopts the random clip mask approach to construct an autoencoder so that MastNet can leverage the power of the strong pre-trained model. Besides, MastNet designs the prediction heads with an auxiliary branch to learn more detailed information in the spatial domain while not causing extra computation burden in the inference. In experiments, the research applies the MastNet on the MovingMNIST and Radar Echo datasets. Our MastNet achieves outstanding results with higher accuracy and longer prediction than current state-of-the-art methods.

![architecture](https://github.com/elesun2018/MastNet/blob/master/attachments/MastNet-fig_arc.jpg "architecture")

### Required packages
We recommend creating a virtual environment and install the required packages by running:
```
pip install -r requirements.txt
```

### Training
You can pass data and save directory via command-line arguments everytime you run an experiment. Alternatively, you can set `Radar_DATA` and `Radar_EXPERIMENTS` environment variables. You can run the following commands:
```
export Radar_DATA=<SPL_DATA>
export Radar_EXPERIMENTS=<path-to-experiment-directory>
export PYTHONPATH=$PYTHONPATH:<path-to-this-repository>
```
Please note that updating `PYTHONPATH` is required while `Radar_DATA` and `Radar_EXPERIMENTS` are optional.
```
cd <path-to-this-repository>
python mastnet/training.py
```
With a unique timestamp, the experiment is stored under `Radar_EXPERIMENTS` or the given target directory if you run the training command with `--data_dir` flag.

### Evaluation
You can evaluate and/or visualize models after training. The following command visualizes clips of 10 frames by evaluating the model on the test dataset with full sequences.
See flags in `mastnet/evaluation.py`. 
```
python mastnet/evaluation.py --model_id <experiment> --visualize
```
Please note that by default the visualization code displays interactive animations using matplotlib. 
TODO: evaluation of the SSIM based metrics may give an error.  
