import subprocess

def runScript(query, nomefile):
    with open("downloader.sh", "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("#SBATCH -N 1\n")
        f.write("#SBATCH -n 1\n")
        f.write("#SBATCH -p g100_all_serial\n")
        f.write("#SBATCH --mem=2GB\n")
        f.write("#SBATCH --time 04:00:00\n")
        f.write("#SBATCH --account elix4_mattiucc_0\n")
#       f.write("#SBATCH --qos=gll_qos_shared\n")
        f.write("#SBATCH --job-name="+nomefile+"\n")
        f.write("#SBATCH --error="+nomefile+".err\n\n\n")
        f.write("esearch -db sra -query \""+query+"\"|efetch -format xml > "+nomefile+".xml\n")
        f.write("sed -i '3s/^/<root> \\n/' "+nomefile+".xml\n")
        f.write("printf '</root>\\n' >> "+nomefile+".xml\n")
    
    proc = subprocess.Popen(["sbatch", "--quiet", "--wait", "downloader.sh"])
    proc.wait()
    
