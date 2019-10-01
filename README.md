# AI2 DARPA Leaderboard Eval Tool

## Environment

- python >= 3.6
- torch
- loguru
- numpy
- pytorch_lightning
- transformers

## Run Your Own Model

### 1. Necessary Implementation

1. Implement your own ModelLoader, TokenizerLoader, and Classifier, similar to those implemented in `huggingface.py`.
2. Change the classifier in both `test.py` as `train.py`

In step 1, when you follow the interface of a `textbook.interface.ModelLoader` or a `textbook.interface.TokenizerLoader`, you will use a `model_type` and `model_weight`
to direct your `load` function to find your model files.

Be sure to make modifications to test_dataset.py (change the tokenizer loader) and run your tokenizer on those datasets!

Later, you can specify the training parameters in `config/hyparams.yaml` in the following format:

```yaml
$task_name:
  $model_type:
    $model_weight:
      seed: 42
      lr: 2e-5
      dropout: 0.1
      batch_size: 32
      max_seq_len: 128
      max_nb_epochs: 3
      initializer_range: 0.02
      weight_decay: 0.0
      warmup_steps: 0
      adam_epsilon: 1e-8
      accumulate_grad_batches: 1
```

You can also specify default parameters within each task.

### 2. Download the datasets

You can use git lfs to pull down all datasets into `./cache` directory.

```bash
git lfs pull
```

### 3. Optional: HuggingFace Pretrained Models

You can also download all the pretrained models from HuggingFace by

```bash
python model_cache.py
```

### 4. Fine Tune the Model

Running train/eval should be straightforward.

```bash
$PYTHON -W ignore train.py --model_type $MODEL_TYPE --model_weight $MODEL_WEIGHT \
  --task_config_file config/tasks.yaml \
  --running_config_file config/hyparams.yaml \
  --task_name $TASK_NAME \
  --task_cache_dir ./cache \
  --output_dir output/$MODEL_TYPE-$MODEL_WEIGHT-$TASK_NAME-pred \
  --log_save_interval 25 --row_log_interval 25
```

Here, $MODEL_TYPE & $MODEL_WEIGHT are names you used to implement your model loader and tokenizer loader; \$TASK_NAME is one of four tasks `{alphanli, hellaswag, physicaliqa, socialiqa}`

During training, it also generates predictions for eval dataset in `output_dir`.

```shell
dev-probabilities.lst
dev-predictions.lst
dev-labels.lst
```

### 5. Eval the model

```bash
$PYTHON -W ignore test.py --model_type $MODEL_TYPE \
  --model_weight $MODEL_WEIGHT \
  --task_name $TASK_NAME \
  --task_config_file config/tasks.yaml \
  --task_cache_dir ./cache \
  --running_config_file config/hyparams.yaml \
  --test_input_dir ./cache/$TASK_NAME-$DATA-input \
  --output_dir output/$MODEL_TYPE-$MODEL_WEIGHT-$TASK_NAME-$DATA-pred \
  --weights_path output/$MODEL_TYPE-$MODEL_WEIGHT-checkpoints/$TASK_NAME/0/_ckpt_epoch_3.ckpt \
  --tags_csv output/$MODEL_TYPE-$MODEL_WEIGHT-log/$TASK_NAME/version_0/meta_tags.csv
```

It should generates all the predcitions in the `output_dir`:

```shell
probabilities.lst
predictions.lst
```
