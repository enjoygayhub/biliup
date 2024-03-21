
import os
import asyncio
import subprocess


def read_files_in_folder(path,end='part'):
    all_files = []
    
    # 列出当前目录下的所有文件
    files = os.listdir(path)
    
    for file in files:
        # 获取完整文件路径
        if file.endswith(end):
            full_path = os.path.join(path, file)
            all_files.append(full_path)
    
    return all_files

# 去掉.part
def rename_parts(names):
    for part in names:
        if os.path.exists(part[0:-5]):
            os.remove(part[0:-5])
        try:
            os.rename(part,part[0:-5])
        except:
            os.remove(part)

async def toMp4(input,output):
    file_name = os.path.basename(input)
    out_name = file_name.replace(".flv",".mp4")
    target = os.path.join(output,out_name)
    print(target)
    args = ['ffmpeg','-i', input, '-c', 'copy', target]
    
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate()
    print(stdout,stderr)
    # 返回标准输出、错误输出和退出代码
    return stdout

    # proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
def transform_parts_to_mp4(folder_path, output_folder= "E:\\videos"):
    all_part = read_files_in_folder(folder_path)
    rename_parts(all_part)
    all_flv = read_files_in_folder(folder_path,'flv')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for file in all_flv:
       asyncio.run(toMp4(file,output_folder)) 
    for file in all_flv:
        os.remove(file)
    pass

if __name__ == '__main__':
   current_dir = os.path.dirname(os.path.abspath(__file__))
   folder_path  = os.path.join(current_dir, '../')
   
   output_folder = "E:\\videos"
   if not os.path.exists(output_folder):
        os.makedirs(output_folder)
   all_part = read_files_in_folder(folder_path)
   rename_parts(all_part)
   all_flv = read_files_in_folder(folder_path,'flv')
   
   for file in all_flv:
       asyncio.run(toMp4(file,output_folder)) 
   for file in all_flv:
        os.remove(file)
   


    



