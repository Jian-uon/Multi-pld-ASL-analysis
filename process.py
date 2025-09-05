import os
import subprocess
import glob
import shutil
from pathlib import Path
import argparse
import nibabel  as nib
import numpy as np
import pandas as pd

join = os.path.join


def get_session_name(dir_name, dicom_dir):

    try:
        
        print(dir_name, dicom_dir)
        print(glob.glob(join(dicom_dir, '*10PLDs_Ctrl*'))[0])
        if dir_name in glob.glob(join(dicom_dir, '*10PLDs_Ctrl*'))[0]:
            return 'ctl'
        elif  dir_name in glob.glob(join(dicom_dir, '*10PLDs_Tag*'))[0]: #'Tag_1003' in dir_name:
            return 'tag'
        elif dir_name in glob.glob(join(dicom_dir, '*10PLDs_M0*'))[0]: #'Tag_1003' in dir_name:'M0_1001' in dir_name:
            return 'm0'
        elif dir_name in glob.glob(join(dicom_dir, '*t1_mx3d_sag_fs_0.6_a5_NIF_*'))[0]:#
            return 't1'
        else:
            return ''
    except Exception as e:
        print(f"Error in get_session_name: {e}")
        return ''

def run_dcm2niix(dicom_dir, output_dir, subject_id, session_name):
    """
    使用dcm2niix转换DICOM到NIfTI格式
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(os.path.join(output_dir, f'{subject_id}_{session_name}.nii')):
        print(f"目录已存在，跳过转换: {os.path.join(output_dir, f'{subject_id}_{session_name}')}")
        return True

    # 构建dcm2niix命令
    cmd = [
        'dcm2niix',
        '-f', f'{subject_id}_{session_name}',  # 输出文件名格式
        '-o', output_dir,                      # 输出目录
        '-b', 'n',                            # 不生成BIDS JSON文件
        '-x', 'y',                             # 压缩输出
        dicom_dir                              # 输入DICOM目录
    ]
    
    print(f"运行命令: {' '.join(cmd)}")
    
    try:
        # 执行转换
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"dcm2niix输出: {result.stdout}")
        
        # 重命名文件（如果需要特定命名）
        #rename_converted_files(output_dir, subject_id, session_name)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"dcm2niix转换失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def run_fsl_oxasl(subject_output_dir, output_dir, subject_id):
    """
    运行FSL oxasl处理ASL数据
    """
    # 确保输出目录存在
    os.makedirs(subject_output_dir, exist_ok=True)
    
    if not os.path.exists(os.path.join(subject_output_dir, f'{subject_id}_asldiff')):
        cmd1 = [
            'fslmaths',
            os.path.join(subject_output_dir, f'{subject_id}_ctl.nii'),
            '-sub',
            os.path.join(subject_output_dir, f'{subject_id}_tag.nii'),
            os.path.join(subject_output_dir, f'{subject_id}_asldiff'),
            
        ]
        print(f"运行命令: {' '.join(cmd1)}")

        try:
            result = subprocess.run(cmd1, capture_output=True, text=True, check=True)
            print(f"fslmerge: {result.stdout}")
            #return True
        except subprocess.CalledProcessError as e:
            print(f"fslmerge处理失败: {e}", subject_id)
            print(f"错误输出: {e.stderr}")
            #return False
    else:
        print(f"asldiff结果已存在，跳过处理: {os.path.join(subject_output_dir, f'{subject_id}_asldiff')}")

    if not os.path.exists(os.path.join(output_dir, 'output','native', 'calib_voxelwise', 'perfusion.nii.gz')):
        # 构建oxasl命令
        cmd = [
            'oxasl',
            '-i', os.path.join(subject_output_dir, f'{subject_id}_asldiff'),          # 输入ASL文件
            '-o', output_dir,     # 输出前缀
            '--casl',                # 假设是CASL序列，根据实际情况调整
            '--bolus=1.8',           # 根据实际情况调整
            '--iaf=diff', 
            '--ibf=rpt',
            '--plds=0.4,0.5,0.7,0.9,1.2,1.5,1.8,2.1,2.4,2.7',
            '-c', os.path.join(subject_output_dir, f'{subject_id}_m0.nii'),
            '--cmethod=voxelwise',
            '--tr', '6.097',  
            '-s', os.path.join(subject_output_dir, f'{subject_id}_t1_Crop_1.nii'),
            '--mc', 
            '--pvcorr',
            '--senscorr',
            '--debug',
            '--region-analysis',
            '--overwrite',
        ]
        
        print(f"运行FSL oxasl命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"oxasl输出: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"oxasl处理失败: {e}", subject_id)
            print(f"错误输出: {e.stderr}")
            return False
        
    else:
        print(f"oxasl结果已存在，跳过处理: {os.path.join(output_dir, 'output','native', 'calib_voxelwise', 'perfusion.nii.gz')}")
    return True


def calculate_gm_signal_curves(subject_output_dir, oxasl_dir, subject_id):
    """
    计算GM partial volume信号曲线
    """
    print(f"计算GM信号曲线 for {subject_id}")
    
    try:
        # 加载必要的文件
        modelfit_mean_file = os.path.join(oxasl_dir,'output', 'native', "modelfit_mean.nii.gz")
        gm_pv_file = os.path.join(oxasl_dir, 'structural', 'gm_pv_asl.nii.gz')
        
        print(modelfit_mean_file)
        print(gm_pv_file)
        
        if not os.path.exists(modelfit_mean_file) or not os.path.exists(gm_pv_file):
            print("缺少必要的处理文件，跳过信号曲线计算")
            return
        
        # 加载图像数据
        modelfit_mean_img = nib.load(modelfit_mean_file)
        gm_pv_img = nib.load(gm_pv_file)
        
        modelfit_mean_data = modelfit_mean_img.get_fdata()
        gm_pv_data = gm_pv_img.get_fdata()
        
        # 获取PLD数量（假设第四维度是PLD）
        if modelfit_mean_data.ndim == 4:
            plds = [0.4,0.5,0.7,0.9,1.2,1.5,1.8,2.1,2.4,2.7]
            n_plds = len(plds)#perfusion_data.shape[3]
            n_repeat = modelfit_mean_data.shape[3]//len(plds)
        else:
            print(" perfusion数据不是4D，跳过信号曲线计算")
            return
        
        # 1. 找到GM partial volume最大的voxel
        max_gm_idx = np.unravel_index(np.argmax(gm_pv_data), gm_pv_data.shape)
        max_gm_signal = modelfit_mean_data[max_gm_idx] 
        
        
        # 2. 找到GM PV > 0.8的所有voxels
        
        gm_mask = gm_pv_data > 0.8
        if np.any(gm_mask):
            # 计算平均信号曲线
            print("Pure gm voxels exist!")
            
            print(modelfit_mean_data.shape)
            if modelfit_mean_data.ndim == 4:
                mean_gm_signal = np.zeros(len(plds))
                for pld in range(len(plds)):
                    mean_gm_signal[pld] = np.mean(modelfit_mean_data[gm_mask, pld])
                print(mean_gm_signal)
            else:
                mean_gm_signal = np.mean(modelfit_mean_data[gm_mask])
        else:
            mean_gm_signal = np.zeros(n_plds) if modelfit_mean_data.ndim == 4 else 0
            print(f"警告: 没有找到GM PV > 0.8的voxels")
        
        # 创建结果DataFrame
        results = []
        for pld in range(n_plds):
            results.append({
                'PLD': plds[pld],
                'Max_GM_PV_Voxel_Signal': max_gm_signal[pld] if isinstance(max_gm_signal, (list, np.ndarray)) else max_gm_signal,
                'Mean_GM_PV_08_Signal': mean_gm_signal[pld] if isinstance(mean_gm_signal, (list, np.ndarray)) else mean_gm_signal
            })
        
        # 保存到CSV
        df = pd.DataFrame(results)
        csv_output = os.path.join(subject_output_dir, f"{subject_id}_delta_M_2_time_curve.csv")
        df.to_csv(csv_output, index=False)
        print(f"GM信号曲线已保存到: {csv_output}")
        
        # 打印统计信息
        print(f"GM PV最大值: {gm_pv_data[max_gm_idx]:.3f}")
        print(f"GM PV > 0.8的voxels数量: {np.sum(gm_mask)}")
        
    except Exception as e:
        print(f"计算GM信号曲线时出错: {e}")


def process_subject(subject_dir, output_base_dir):
    """
    处理单个subject的所有DICOM文件夹
    """
    subject_id = os.path.basename(subject_dir.rstrip('/'))
    print(f"****************************************************************")
    print(f"开始处理subject: {subject_id}")
    print(f"****************************************************************")
    # 创建subject的输出目录
    subject_output_dir = os.path.join(output_base_dir, subject_id)
    os.makedirs(subject_output_dir, exist_ok=True)
    
    # 查找所有DICOM文件夹
    dicom_dirs = []
    for item in os.listdir(subject_dir):
        item_path = os.path.join(subject_dir, item)
        if os.path.isdir(item_path):
            # 检查是否是DICOM文件夹（可以根据需要添加更精确的检查）
            dicom_dirs.append((item, item_path))
    
    print(f"找到 {len(dicom_dirs)} 个DICOM文件夹")
    
    # 第一步：转换所有DICOM文件夹
    converted_files = []
    for session_name, dicom_dir in dicom_dirs:
        print(f"转换DICOM文件夹: {session_name}")
        new_name = get_session_name(session_name, subject_dir)
        if new_name == '': continue
        completed = run_dcm2niix(dicom_dir, subject_output_dir, subject_id, new_name)
        if completed:
            # 查找转换后的ASL文件（可能需要根据实际文件名模式调整）
            nii_files = glob.glob(os.path.join(subject_output_dir, f"{subject_id}_{new_name}.nii*"))
            converted_files.extend(nii_files)
    
    #print(f"处理ASL文件: {asl_file}")    
    # 创建oxasl输出目录
    oxasl_output_dir = os.path.join(subject_output_dir, 'oxasl_results')
        
    run_fsl_oxasl(subject_output_dir, oxasl_output_dir, subject_id)
    
    calculate_gm_signal_curves(subject_output_dir, oxasl_output_dir, subject_id)

def main():
    parser = argparse.ArgumentParser(description='处理ASL数据集')
    parser.add_argument('input_dir', help='包含所有subject的输入目录')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--subject', help='处理单个subject（可选）')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.subject:
        # 处理单个subject
        subject_dir = os.path.join(args.input_dir, args.subject)
        if os.path.exists(subject_dir):
            process_subject(subject_dir, args.output_dir)
        else:
            print(f"Subject目录不存在: {subject_dir}")
    else:
        # 处理所有subject
        for item in os.listdir(args.input_dir):
            subject_dir = os.path.join(args.input_dir, item)
            if os.path.isdir(subject_dir):
                process_subject(subject_dir, args.output_dir)

if __name__ == "__main__":
    main()