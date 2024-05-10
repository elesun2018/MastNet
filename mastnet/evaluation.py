"""


This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import glob
import json
import argparse

import numpy as np
import tensorflow as tf

from spl.data.amass_tf import TFRecordMotionDataset
from spl.model.zero_velocity import ZeroVelocityBaseline
from spl.model.rnn import RNN
from spl.model.seq2seq import Seq2SeqModel
from spl.model.transformer import Transformer2d
from spl.model.transformer_h36m import Transformer2d as Transformer2dH36M
from spl.model.vanilla import Transformer1d

from common.constants import Constants as C
from visualization.render import Visualizer
from visualization.fk import H36MForwardKinematics
from visualization.fk import SMPLForwardKinematics
import seaborn as sn
import pandas as pd
from metrics.motion_metrics import MetricsEngine
import matplotlib.pyplot as plt

plt.switch_backend('agg')


sample_keys_amass = [
    # Additional samples
    # "Eyes/0/Eyes/kaiwawalk_SB2_03_SB2_sneak_SB2_kaiwa_dynamics",
    # "Eyes/0/Eyes/kaiwaturn_SB2_02_SB2_look_SB_around_SB2_kaiwa_dynamics",
    # "Eyes/0/Eyes/hamashowalk_SB2_06_SB2_catwalk_SB2_hamasho_dynamics",
    # "Eyes/0/Eyes/ichigepose_SB2_20_SB2_zombee_SB2_ichige_dynamics",
    # "Eyes/0/Eyes/kudowalk_SB2_07_SB2_moonwalk_SB2_kudo_dynamics",
    # "BioMotion/0/BioMotion/rub0390000_treadmill_norm_dynamics",
    # "BioMotion/0/BioMotion/rub0680000_treadmill_norm_dynamics",
    # "BioMotion/0/BioMotion/rub0420028_scamper_dynamics"
    # "Eyes/0/Eyes/hamashogesture_etc_SB2_20_SB2_swing_SB_chair_SB2_hamasho_dynamics",
    # "HDM05/0/HDM05/bdHDM_bd_03_SB2_02_02_120_dynamics",
    # "Eyes/0/Eyes/shionojump_SB2_10_SB2_rope_SB_long_SB2_shiono_dynamics",
    # # Shorter than 1200 steps.
    # "CMU/0/CMU/136_136_18",
    # "CMU/0/CMU/143_143_23",  # punching
    # "BioMotion/0/BioMotion/rub0700002_treadmill_slow_dynamics",
    # "BioMotion/0/BioMotion/rub0220001_treadmill_fast_dynamics",
    # # Longer than 1200
    # "BioMotion/0/BioMotion/rub0640003_treadmill_jog_dynamics",
    # "BioMotion/0/BioMotion/rub1110002_treadmill_slow_dynamics",
    # "BioMotion/0/BioMotion/rub1030000_treadmill_norm_dynamics",
    # "BioMotion/0/BioMotion/rub0800029_scamper_dynamics",
    # "BioMotion/0/BioMotion/rub0830021_catching_and_throwing_dynamics",
    # "Eyes/0/Eyes/kaiwajump_SB2_06_SB2_rope_SB_normal_SB_run_SB_fast_SB2_kaiwa_dynamics",
    # "Eyes/0/Eyes/yokoyamathrow_toss_SB2_01_SB2_over_SB2_yokoyama_dynamics",
    
    # "BioMotion/0/BioMotion/rub0830021_catching_and_throwing_dynamics",
    # "CMU/0/CMU/143_143_23",
    # "Eyes/0/Eyes/yokoyamathrow_toss_SB2_01_SB2_over_SB2_yokoyama_dynamics",
    # "BioMotion/0/BioMotion/rub0640003_treadmill_jog_dynamics",
    # "BioMotion/0/BioMotion/rub0410003_treadmill_jog_dynamics",
    # "BioMotion/0/BioMotion/rub0290000_treadmill_norm_dynamics",
    # "BioMotion/0/BioMotion/rub0830029_jumping2_dynamics",
    # "BioMotion/0/BioMotion/rub0150028_circle_walk_dynamics",
    # "BioMotion/0/BioMotion/rub0050003_treadmill_jog_dynamics",
    # "Eyes/0/Eyes/hamadajump_SB2_12_SB2_boxer_SB_step_SB2_hamada_dynamics",
    # "Eyes/0/Eyes/azumithrow_toss_SB2_06_SB2_both_SB_hands_SB_under_SB_light_SB2_azumi_dynamics",
    # "ACCAD/0/ACCAD/Female1Running_c3dC4_SB__SB2__SB_Run_SB_to_SB_walk1_dynamics",
    # "ACCAD/0/ACCAD/Male1Running_c3dRun_SB_C27_SB__SB2__SB_crouch_SB_to_SB_run_dynamics",
    # "Transition/0/Transition/mazen_c3djumpingjacks_turntwist180",
    # "Transition/0/Transition/mazen_c3dJOOF_runbackwards",
    
    "BioMotion/0/BioMotion/rub0290000_treadmill_norm_dynamics",
    "ACCAD/0/ACCAD/Male1Running_c3dRun_SB_C27_SB__SB2__SB_crouch_SB_to_SB_run_dynamics",
    "HDM05/0/HDM05/bdHDM_bd_03_SB2_02_02_120_dynamics",
    "BioMotion/0/BioMotion/rub0640003_treadmill_jog_dynamics",
    ]


sample_keys_h36m = [
        "h36/0/S9_walkingd",
        "h36/0/S7_discussi",
        "h36/0/S9_smoki",
        "h36/0/S6_walkingd",
        "h36/0/S11_sitti",
        "h36/0/S11_walkingtogeth"
        ]

try:
    from common.logger import GoogleSheetLogger

    if "GLOGGER_WORKBOOK_AMASS" not in os.environ:
        raise ImportError("GLOGGER_WORKBOOK_AMASS not found.")
    if "GDRIVE_API_KEY" not in os.environ:
        raise ImportError("GDRIVE_API_KEY not found.")
    GLOGGER_AVAILABLE = True
except ImportError:
    GLOGGER_AVAILABLE = False
    print("GLogger not available...")


def load_latest_checkpoint(session, saver, experiment_dir):
    """Restore the latest checkpoint found in `experiment_dir`."""
    ckpt = tf.train.get_checkpoint_state(experiment_dir, latest_filename="checkpoint")

    if ckpt and ckpt.model_checkpoint_path:
        # Check if the specific checkpoint exists
        ckpt_name = os.path.basename(ckpt.model_checkpoint_path)
        print("Loading model checkpoint {0}".format(ckpt_name))
        saver.restore(session, ckpt.model_checkpoint_path)
    else:
        raise (ValueError, "Checkpoint {0} does not seem to exist".format(ckpt.model_checkpoint_path))


def get_model_cls(model_type, is_h36m=False):
    if model_type == C.MODEL_ZERO_VEL:
        return ZeroVelocityBaseline
    elif model_type == C.MODEL_RNN:
        return RNN
    elif model_type == C.MODEL_SEQ2SEQ:
        return Seq2SeqModel
    elif model_type == C.MODEL_TRANS2D and is_h36m:
        return Transformer2dH36M
    elif model_type == C.MODEL_TRANS2D:
        return Transformer2d
    elif model_type == "transformer1d":
        return Transformer1d
    else:
        raise Exception("Unknown model type.")


def create_and_restore_model(session, experiment_dir, data_dir, config, dynamic_test_split):
    model_cls = get_model_cls(config["model_type"], config["use_h36m"])
    print("Using model " + model_cls.__name__)

    window_length = config["source_seq_len"] + config["target_seq_len"]
    sample_keys = sample_keys_amass
    if config["use_h36m"]:
        data_dir = os.path.join(data_dir, '../h3.6m/tfrecords/')
        sample_keys = sample_keys_h36m

    if dynamic_test_split:  # For visualization
        data_split = "test_dynamic"
        filter_sample_keys = sample_keys
        beginning_index = 0
        window_type = C.DATA_WINDOW_CENTER
    else:  # For quantitative evaluation.
        data_split = "test"
        filter_sample_keys = None
        default_seed_len = 120
        if config["use_h36m"]:
            default_seed_len = 50
        beginning_index = default_seed_len - config["source_seq_len"]
        window_type = C.DATA_WINDOW_BEGINNING

    test_data_path = os.path.join(data_dir, config["data_type"], data_split, "amass-?????-of-?????")
    meta_data_path = os.path.join(data_dir, config["data_type"], "training", "stats.npz")
    print("Loading test data from " + test_data_path)
    
    # Create dataset.
    with tf.name_scope("test_data"):
        window_length = config["source_seq_len"] + config["target_seq_len"]
        test_data = TFRecordMotionDataset(data_path=test_data_path,
                                          meta_data_path=meta_data_path,
                                          batch_size=config["batch_size"]*2,
                                          shuffle=False,
                                          extract_windows_of=window_length,
                                          window_type=window_type,
                                          num_parallel_calls=4,
                                          normalize=not config["no_normalization"],
                                          normalization_dim=config.get("normalization_dim", "channel"),
                                          use_std_norm=config.get("use_std_norm", False),
                                          beginning_index=beginning_index,
                                          filter_by_key=filter_sample_keys,
                                          apply_length_filter=False)
        test_pl = test_data.get_tf_samples()

    # Create model.
    with tf.name_scope(C.TEST):
        test_model = model_cls(
            config=config,
            data_pl=test_pl,
            mode=C.SAMPLE,
            reuse=False)
        test_model.build_graph()
        test_model.summary_routines()

    num_param = 0
    for v in tf.trainable_variables():
        num_param += np.prod(v.shape.as_list())
    print("# of parameters: " + str(num_param))

    # Restore model parameters.
    saver = tf.train.Saver(tf.global_variables(), max_to_keep=1, save_relative_paths=True)
    load_latest_checkpoint(session, saver, experiment_dir)
    return test_model, test_data


def evaluate_model(session, _eval_model, _eval_iter, _metrics_engine,
                   undo_normalization_fn, _return_results=False):
    # make a full pass on the validation or test dataset and compute the metrics
    n_batches = 0
    _eval_result = dict()
    _metrics_engine.reset()
    _attention_weights = dict()
    session.run(_eval_iter.initializer)

    using_attention_model = False
    if isinstance(_eval_model, Transformer2d) or isinstance(_eval_model, Transformer2dH36M):
        print("Using Attention Model.")
        using_attention_model = True
    
    try:
        while True:
            # Get the predictions and ground truth values
            res = _eval_model.sampled_step(session)
            if using_attention_model:
                prediction, targets, seed_sequence, data_id, attention = res
            else:
                prediction, targets, seed_sequence, data_id = res
            # Unnormalize predictions if there normalization applied.
            p = undo_normalization_fn(
                {"poses": prediction}, "poses")
            t = undo_normalization_fn(
                {"poses": targets}, "poses")
            _metrics_engine.compute_and_aggregate(p["poses"], t["poses"])

            if _return_results:
                s = undo_normalization_fn(
                    {"poses": seed_sequence}, "poses")
                # Store each test sample and corresponding predictions with
                # the unique sample IDs.
                for k in range(prediction.shape[0]):
                    _eval_result[data_id[k].decode("utf-8")] = (
                        p["poses"][k],
                        t["poses"][k],
                        s["poses"][k])

                if using_attention_model:
                    for num_frame in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
                        if num_frame <= prediction.shape[1]:
                            for i in range(prediction.shape[0]):
                                if num_frame == 0:
                                    _attention_weights[data_id[i].decode("utf-8")] = [[attention[num_frame]['temporal'][i], attention[num_frame]['spatial'][i]]]
                                else:
                                    _attention_weights[data_id[i].decode("utf-8")] += [[attention[num_frame]['temporal'][i], attention[num_frame]['spatial'][i]]]
                n_batches += 1
            
            if n_batches % 5 == 0:
                print("Evaluated on {} batches...".format(n_batches))
            
    except tf.errors.OutOfRangeError:
        pass
    print("Evaluated on " + str(n_batches) + " batches.")
        # finalize the computation of the metrics
    final_metrics = _metrics_engine.get_final_metrics()
    return final_metrics, _eval_result, _attention_weights

def visualize_temporal(mat, save_path, num_frame):
    # mat: (num_layers, num_joints, num_heads, seq_len)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    fig = plt.figure()
    num_layers = mat.shape[0]
    num_joints = mat.shape[1]
    num_heads = mat.shape[2]
    seq_len = mat.shape[3]
    for layer_idx in range(num_layers):
        for head_idx in range(num_heads):
            ax = fig.add_subplot(num_layers, num_heads, layer_idx * num_heads + head_idx + 1)
            ax.axis('off')
            array = mat[layer_idx, :, head_idx, :]  # (num_joints, seq_len)
            df_cm = pd.DataFrame(array, index=[(i+1) for i in range(num_joints)], columns=[(i+1) for i in range(seq_len)])
            sn.heatmap(df_cm, annot=False, cmap="YlGnBu", ax=ax, vmin=0.0, vmax=1.0, cbar=False)

    fig.savefig(os.path.join(save_path, 'temporal_attn' + str(num_frame) + '.png'))
    plt.close(fig)
    plt.clf()

    for layer_idx in range(num_layers):
        for head_idx in range(num_heads):
            array = mat[layer_idx, :, head_idx, :]  # (num_joints, seq_len)
            df_cm = pd.DataFrame(array, index=[(i+1) for i in range(num_joints)], columns=[(i+1) for i in range(seq_len)])
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            sn.heatmap(df_cm, annot=False, cmap="YlGnBu", vmin=0.0, vmax=1.0, ax=ax)
            fig.savefig(os.path.join(save_path,
                                     'temporal_' + 'layer_' + str(layer_idx) + 'head_' + str(head_idx) + '_' + str(
                                         num_frame) + '.png'))
            plt.close(fig)
            plt.clf()


def visualize_spatial(mat, save_path, num_frame):
    # mat: (num_layers, num_heads, num_joints, num_joints)
    fig = plt.figure()
    num_layers = mat.shape[0]
    num_heads = mat.shape[1]
    num_joints = mat.shape[2]
    for layer_idx in range(num_layers):
        for head_idx in range(num_heads):
            ax = fig.add_subplot(num_layers, num_heads, layer_idx * num_heads + head_idx + 1)
            ax.axis('off')
            array = mat[layer_idx, head_idx, :, :]  # (num_joints, num_joints)
            df_cm = pd.DataFrame(array, index=[(i+1) for i in range(num_joints)], columns=[(i+1) for i in range(num_joints)])
            sn.heatmap(df_cm, annot=False, cmap="YlGnBu", ax=ax, vmin=0.0, vmax=1.0, cbar=False)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    plt.axis('off')
    fig.savefig(os.path.join(save_path, 'spatial_attn' + str(num_frame) + '.png'))
    plt.close(fig)
    plt.clf()

    for layer_idx in range(num_layers):
        for head_idx in range(num_heads):
            array = mat[layer_idx, head_idx, :, :]  # (num_joints, num_joints)
            df_cm = pd.DataFrame(array, index=[i for i in range(num_joints)], columns=[i for i in range(num_joints)])
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            sn.heatmap(df_cm, annot=False, cmap="YlGnBu", vmin=0.0, vmax=1.0, ax=ax)
            fig.savefig(os.path.join(save_path,
                                     'spatial_' + 'layer_' + str(layer_idx) + 'head_' + str(head_idx) + '_' + str(
                                         num_frame) + '.png'))
            plt.close(fig)
            plt.clf()


def evaluate(session, test_model, test_data, args, eval_dir, use_h36m):
    test_iter = test_data.get_iterator()

    using_attention_model = False
    if isinstance(test_model, Transformer2d) or isinstance(test_model, Transformer2dH36M):
        using_attention_model = True

    # Create metrics engine including summaries
    pck_thresholds = C.METRIC_PCK_THRESHS
    if use_h36m:
        fk_engine = H36MForwardKinematics()
        target_lengths = [x for x in C.METRIC_TARGET_LENGTHS_H36M if x <= test_model.target_seq_len]
        sample_keys = sample_keys_h36m
    else:
        fk_engine = SMPLForwardKinematics()
        target_lengths = [x for x in C.METRIC_TARGET_LENGTHS_AMASS if x <= test_model.target_seq_len]
        sample_keys = sample_keys_amass
    
    representation = C.QUATERNION if test_model.use_quat else C.ANGLE_AXIS if test_model.use_aa else C.ROT_MATRIX
    metrics_engine = MetricsEngine(fk_engine,
                                   target_lengths,
                                   force_valid_rot=True,
                                   pck_threshs=pck_thresholds,
                                   rep=representation)
    # create the necessary summary placeholders and ops
    metrics_engine.create_summaries()
    # reset computation of metrics
    metrics_engine.reset()

    # Google logging.
    if args.glog_entry and GLOGGER_AVAILABLE:
        exp_id = os.path.split(eval_dir)[-1].split("-")[0]
        glogger_workbook = os.environ["GLOGGER_WORKBOOK_AMASS"]
        gdrive_key = os.environ["GDRIVE_API_KEY"]
        model_name = '-'.join(os.path.split(eval_dir)[-1].split('-')[1:])
        static_values = dict()
        # exp_id = exp_id + "-W" + str(args.seq_length_in)
        static_values["Model ID"] = exp_id
        static_values["Model Name"] = model_name

        credentials = tf.gfile.Open(gdrive_key, "r")
        glogger = GoogleSheetLogger(
            credentials,
            glogger_workbook,
            sheet_names=["until_{}".format(24)],
            model_identifier=exp_id,
            static_values=static_values)

    print("Evaluating test set...")
    test_metrics, eval_result, attention_weights = evaluate_model(session,
                                                                  test_model,
                                                                  test_iter,
                                                                  metrics_engine,
                                                                  test_data.unnormalization_func,
                                                                  _return_results=True)

    print(metrics_engine.get_summary_string_all(test_metrics, target_lengths,
                                                pck_thresholds))

    # If there is a new checkpoint, log the result.
    if args.glog_entry and GLOGGER_AVAILABLE:
        for t in metrics_engine.target_lengths:
            eval_ = metrics_engine.get_metrics_until(test_metrics,
                                                     t,
                                                     pck_thresholds,
                                                     prefix="test ")
            glogger.update_or_append_row(eval_,
                                         "until_{}".format(t))

    if args.visualize:
        data_representation = "quat" if test_model.use_quat else "aa" if test_model.use_aa else "rotmat"
        # visualize some random samples stored in `eval_result` which is a
        # dict id -> (prediction, seed, target)
        if not args.to_video:
            visualizer = Visualizer(interactive=True, fk_engine=fk_engine,
                                    rep=data_representation)
        else:
            visualizer = Visualizer(interactive=False, fk_engine=fk_engine,
                                    rep=data_representation,
                                    output_dir=eval_dir,
                                    skeleton=not args.no_skel,
                                    dense=not args.no_mesh,
                                    to_video=args.to_video,
                                    keep_frames=False)

        # Find an entry by name
        # idxs = [i for i in range(32)]
        # sample_keys = [list(sorted(eval_result.keys()))[i] for i in idxs]
        
        print("Visualizing samples...")
        for i, k in enumerate(sample_keys):
            if k in eval_result:
                title = k
                fname = title.replace('/', '.')
                fname = fname.split('_')[0]  # reduce name otherwise stupid OSes (i.e., all of them) can't handle it
                dir_prefix = 'skeleton'
                out_dir = os.path.join(eval_dir, dir_prefix, fname)
                
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                
                print(out_dir + ' visualizing.')

                # if using_attention_model:
                #     for num_frame in range(12):
                #         visualize_temporal(attention_weights[k][num_frame][0], out_dir, num_frame*5)
                #         visualize_spatial(attention_weights[k][num_frame][1], out_dir, num_frame*5)

                prediction, target, seed = eval_result[k]

                heat = np.transpose(prediction)
                fig = plt.figure()
                ax = fig.add_subplot(1, 1, 1)
                sn.heatmap(heat, ax=ax, annot=False, vmin=-1.0, vmax=1.0, cmap='YlGnBu')
                ax.set(aspect=1)
                plt.axis('off')
                fig.savefig(os.path.join(out_dir, 'whole.png'))
                plt.close(fig)
                plt.clf()
                np.save(os.path.join(out_dir, 'whole.npy'), heat)

                len_diff = prediction.shape[0] - target.shape[0]
                if len_diff > 0:
                    target = np.concatenate([target, np.tile(target[-1:], (len_diff, 1))], axis=0)
                visualizer.visualize_results(seed, prediction, target,
                                             title=k + "_i{}".format(i))
            else:
                print("Sequence " + k + " not found!")


if __name__ == '__main__':
    # If you would like to quantitatively evaluate a model, then
    # --dynamic_test_split shouldn't be passed. In this case, the model will be
    # evaluated on 180 frame windows extracted from the entire test split.
    # You can still visualize samples. However, number of predicted frames
    # will be less than or equal to 60. If you intend to evaluate/visualize
    # longer predictions, then you should pass --dynamic_test_split which
    # enables using original full-length test sequences. Hence,
    # --seq_length_out can be much longer than 60.

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_id', required=True, default=None, type=str,
                        help="Experiment ID (experiment timestamp) or "
                             "comma-separated list of ids.")
    parser.add_argument('--eval_dir', required=False, default=None, type=str,
                        help="Main visualization directory. First, a folder "
                             "with the experiment name is created inside. "
                             "If not passed, then save_dir is used.")
    parser.add_argument('--save_dir', required=False, default=None, type=str,
                        help="Path to experiments. If not passed, "
                             "then AMASS_EXPERIMENTS environment variable is "
                             "used.")
    parser.add_argument('--data_dir', required=False, default=None, type=str,
                        help="Path to data. If not passed, "
                             "then AMASS_DATA environment variable is used.")

    parser.add_argument('--seq_length_in', required=False, type=int,
                        help="Seed sequence length")
    parser.add_argument('--seq_length_out', required=False, type=int,
                        help="Target sequence length")
    parser.add_argument('--batch_size', required=False, default=64, type=int,
                        help="Batch size")

    parser.add_argument('--visualize', required=False, action="store_true",
                        help="Visualize ground-truth and predictions "
                             "side-by-side by using human skeleton.")
    parser.add_argument('--no_skel', required=False, action="store_true",
                        help="Dont show skeleton in offline visualization.")
    parser.add_argument('--no_mesh', required=False, action="store_true",
                        help="Dont show mesh in offline visualization")
    parser.add_argument('--to_video', required=False, action="store_true",
                        help="Save the model predictions to mp4 videos in the "
                             "experiments folder.")
    parser.add_argument('--dynamic_test_split', required=False,
                        action="store_true",
                        help="Test samples are extracted on-the-fly.")
    parser.add_argument('--glog_entry', required=False,
                        action="store_true",
                        help="Create a Google sheet entry if available.")
    parser.add_argument('--new_experiment_id', required=False, default=None,
                        type=str, help="Not used. only for leonhard.")

    _args = parser.parse_args()
    if ',' in _args.model_id:
        model_ids = _args.model_id.split(',')
    else:
        model_ids = [_args.model_id]

    # Set experiment directory.
    _save_dir = _args.save_dir if _args.save_dir else os.environ["AMASS_EXPERIMENTS"]
    # Set data paths.
    _data_dir = _args.data_dir if _args.data_dir else os.environ["AMASS_DATA"]

    # Run evaluation for each model id.
    for model_id in model_ids:
        try:
            _experiment_dir = glob.glob(os.path.join(_save_dir, model_id + "-*"), recursive=False)[0]
        except IndexError:
            print("Model " + str(model_id) + " is not found in " + str(_save_dir))
            continue

        try:
            tf.reset_default_graph()
            _config = json.load(open(os.path.abspath(os.path.join(_experiment_dir, 'config.json')), 'r'))
            _config["experiment_dir"] = _experiment_dir

            if _args.seq_length_out is not None and _config["target_seq_len"] != _args.seq_length_out:
                print("!!! Prediction length for training and sampling is different !!!")
                _config["target_seq_len"] = _args.seq_length_out

            if _args.seq_length_in is not None and _config["source_seq_len"] != _args.seq_length_in:
                print("!!! Seed sequence length for training and sampling is different !!!")
                _config["source_seq_len"] = _args.seq_length_in

            gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.9, allow_growth=True)
            with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)) as sess:
                exp_name = os.path.split(_experiment_dir)[-1]
                _eval_dir = _experiment_dir if _args.eval_dir is None else os.path.join(_args.eval_dir, exp_name)
                if not os.path.exists(_eval_dir):
                    os.mkdir(_eval_dir)
                _test_model, _test_data = create_and_restore_model(sess, _experiment_dir, _data_dir, _config,
                                                                   _args.dynamic_test_split)
                print("Evaluating Model " + str(model_id))
                evaluate(sess, _test_model, _test_data, _args, _eval_dir, _config["use_h36m"])

                # _eval_iter = _test_data.get_iterator()
                # sess.run(_eval_iter.initializer)
                # n_samples = 0
                # try:
                #     while True:
                #         data_ids, data_samples = sess.run([_test_model.data_ids, _test_model.data_inputs])
                #         for id_ in data_ids:
                #             print(id_)
                #             n_samples += 1
                # except tf.errors.OutOfRangeError:
                #     pass
                # print("# samples: " + str(n_samples))
                
        except Exception as e:
            print("Something went wrong when evaluating model {}".format(model_id))
            raise Exception(e)
