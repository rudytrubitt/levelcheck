import os
import subprocess
import json
from operator import itemgetter
import sys
import re

version = "levelcheck 2019-03-20 by rudy trubitt"
''' 
levelcheck is a python program written by rudy trubitt, rudy@trubitt.com

see README.md for installation, usage and limitations

'''

def main():
    check_dependencies()
    print(version)
    working_dir = "./" #  needs trailing slash for proper concatenation
    statsdir = '_levelcheckfiles/' # local folder for storing levelcheck text files
    statspath = working_dir + statsdir

    if os.path.isdir(statspath):  # check if statpath exists, create if missing
        pass # local statpath folder exists!
    else:  # create the stats folder
        os.makedirs(statspath)

    clean_files(statspath) # remove all stats files from a previous run, if present


    snd_files = [i for i in os.listdir(working_dir) if i.endswith(".wav")]  # list wav files
    #todo test for the condition where there are no .wav files in the current working directory
    for snd_file in snd_files:
        # main loop through the list wav files in working directory. Next,
        # process some paths and filenames, then run sox and ffmpeg on snd_file_handle
        snd_file_no_ext = snd_file.replace(".wav", "") #new var, strip .wav extension from filename
        snd_file_handle = working_dir + snd_file
        stat_file_handle = statsdir + snd_file_no_ext + ".json"  # full path to stat json file


        snd_stats = get_sox_stats_on_file(snd_file_handle)  # Run sox on the snd_file
        sox_stats_to_json(snd_file_handle, snd_stats, stat_file_handle)  # Parse sox output, convert to json
        # todo refactor to split large function in half, create  write_json_to_file(data,f)
        ffmpeg_lufs_to_file(snd_file_handle, statspath, snd_file_no_ext)  # parse_lufs_from_ffmpeg(ffmpeg_stats)

    view_results(statspath)


def check_dependencies():
    pass
    #todo - test for presence of python3 the executable sox and ffmpeg, raise exception if missing


def clean_files(statspath):
    #todo - could improve by deleting only if matching .wav absent or has newer modification date
    def purge(statspath, pattern):
        for f in os.listdir(statspath):
            if re.search(pattern, f):
                os.remove(os.path.join(statspath, f))

    purge(statspath, '.json')
    purge(statspath, '.lufs')


def view_results(statspath):
    # Display results. Reads individual sox/json files and adds each object to a list
    # then sort the list on sox RMS values. Incorporating the lufs result is
    # kind of a hack, it would be better to add that result to the json file.

    json_files = [i for i in os.listdir(statspath) if i.endswith(".json")]
    json_results = [] # initialize list to append each json key/value data structure

    for json_file in json_files:
        file_handle = statspath + json_file

        with open(file_handle) as json_data:
            data = json.load(json_data)
            #print(json_result)
            json_results.append(data)


    rms_sort_json_results = sorted(json_results, key=itemgetter('RMS_lev_dB'), reverse=False) # Create a list of dicts

    for json_result in rms_sort_json_results:
        # iterate through RMS sorted list and also grab the LUFs value so we can report that too.
        # first determine the lufs filename so we can open and read it
        lufs_filename_wav = (json_result.get('Filename'))
        lufs_filehandle = statspath + lufs_filename_wav.replace(".wav",".lufs")


        with open(lufs_filehandle, 'r') as lufs_file:  # Open the lufs file for reading
            raw_lufs_text = lufs_file.read()

        lufs_array = (raw_lufs_text.split(","))
        lufs_key_val = (lufs_array[-8])
        lufs = (lufs_key_val.split(" ")[-2])

        # print RPM, LUFS and file_handle!
        print(json_result.get('RMS_lev_dB'), 'dB RMS,', lufs, 'dB LUFS,', (json_result.get('Filename')))


def get_sox_stats_on_file(file_handle):
    sox_call = subprocess.Popen(["sox", file_handle, "-n", "stats"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sox_call.communicate()
    file_stats_one_line = (stderr.decode("utf-8"))
    file_stats = (file_stats_one_line.splitlines())
    return file_stats


def sox_stats_to_json(snd_file_handle, file_stats, stat_file_handle):
    """takes the stderror result of sox -stats command and converts to json format"""

    ''' STEP 1'''

    num_stats = len(file_stats)
    temp_var = ""

    #print(file_stats)
    stats_to_json_step1 = []
    for i in range(num_stats):
        '''this NOT DRY chunk of code manually turns sox stat descriptions into 
        single words/no spaces and inserts a delimiter string (3 underscores)
        after keyword and appends result to a new list called stats_to_json_step1
        TODO refactor this to make more DRY and trap for new descriptions which,
        if present, will be silently deleted in this code'''
        # TODO deal with stereo files, currently prints a warning
        temp_var = (file_stats[i])

        if 'DC offset' in temp_var:
            fixed = temp_var.replace('DC offset', 'DC_Offset ___')
            stats_to_json_step1.append(fixed)

        elif 'Min level' in temp_var:
            fixed = temp_var.replace('Min level', 'Min_level ___')
            stats_to_json_step1.append(fixed)

        elif 'Max level' in temp_var:
            fixed = temp_var.replace('Max level', 'Max_level ___')
            stats_to_json_step1.append(fixed)

        elif 'Pk lev dB' in temp_var:
            fixed = temp_var.replace('Pk lev dB', 'Pk_lev_dB ___')
            stats_to_json_step1.append(fixed)

        elif 'RMS lev dB' in temp_var:
            fixed = temp_var.replace('RMS lev dB', 'RMS_lev_dB ___')
            stats_to_json_step1.append(fixed)

        elif 'RMS Pk dB' in temp_var:
            fixed = temp_var.replace('RMS Pk dB', 'RMS_Pk_dB ___')
            stats_to_json_step1.append(fixed)

        elif 'RMS Tr dB' in temp_var:
            fixed = temp_var.replace('RMS Tr dB', 'RMS_Tr_dB ___')
            stats_to_json_step1.append(fixed)

        elif 'Crest factor' in temp_var:
            fixed = temp_var.replace('Crest factor', 'Crest_factor ___')
            stats_to_json_step1.append(fixed)

        elif 'Flat factor' in temp_var:
            fixed = temp_var.replace('Flat factor', 'Flat_factor ___')
            stats_to_json_step1.append(fixed)

        elif 'Pk count' in temp_var:
            fixed = temp_var.replace('Pk count', 'Pk_count ___')
            stats_to_json_step1.append(fixed)

        elif 'Bit-depth' in temp_var:
            fixed = temp_var.replace('Bit-depth', 'Bit_depth ___')
            stats_to_json_step1.append(fixed)

        elif 'Num samples' in temp_var:
            fixed = temp_var.replace('Num samples', 'Num_samples ___')
            stats_to_json_step1.append(fixed)
            #print(fixed)
        elif 'Length s' in temp_var:
            fixed = temp_var.replace('Length s', 'Length_s ___')
            stats_to_json_step1.append(fixed)

        elif 'Scale max' in temp_var:
            fixed = temp_var.replace('Scale max', 'Scale_max ___')
            stats_to_json_step1.append(fixed)

        elif 'Window s' in temp_var:
            fixed = temp_var.replace('Window s', 'Window_s ___')
            stats_to_json_step1.append(fixed)

        elif 'Overall     Left      Right' in temp_var:
            pass # avoid generating warning, we will grab overall value later

        else: # issue a warning for anything we are not specifically checking for!
            print("WARNING: unrecognized stats ignored in file", file, ":", temp_var)

    # print(stats_to_json_step1) for debug

    ''' STEP 2'''
    #todo should refactor this to make the writing file a separate def
    stats_to_json_step2=[] # initialize a list to hold the results as we append
    # Open the JSON data block and write a key/value pair for filename
    json_file = open(stat_file_handle, "w")
    #print(json_file)
    line_to_write = "" # initialize a temp variable called line_to_write
    print( "{", file =  json_file)
    print("\"" + "Filename" + "\"" , ':' , "\"" + snd_file_handle + "\"",',', file = json_file)
    num_stats1 = len(stats_to_json_step1)



    '''
    In this section, we grab the key and value strings and put them in our data structure
    '''
    for i in range(num_stats1):
        temp_var = stats_to_json_step1[i]
        my_key_spaces = (temp_var.split('___')[0])
        my_value_spaces = (temp_var.split('___')[1])
        '''
        In case of stereo files, there are three values listed for many stats. The first is "overall"
        and that's the only one we want. So we want to split values and use the
        0th item in all cases.
        '''
        list_of_values = my_value_spaces.split()
        item_zero_values = (list_of_values[0])




        my_key = my_key_spaces.replace(" ", "")  # Remove the spaces from key and value strings
        my_value = item_zero_values.replace(" ", "")
        if i < (num_stats1 - 1):
            # Finally,  format the json key/value pair of strings with colon delimiter
            print("\"" + my_key + "\"" , ':' , "\"" + my_value + "\"",',', file = json_file)
        else:
            # for the last line, must supress the trailing comma, so if test here...
            print("\"" + my_key + "\"", ':', "\"" + my_value + "\"", file = json_file)
            print('}', file = json_file)  # Close the JSON data block
    json_file.close


def ffmpeg_lufs_to_file(snd_file_handle, statspath, snd_file_no_ext):
    '''
    Runs ffmpeg on file_handle to get LUFS report and writes the resulting list as a string to file_handle.lufs for subsequent reporting
    '''
    ffmpeg_call = subprocess.Popen(["ffmpeg", "-nostats",  "-i", snd_file_handle, "-filter_complex" ,  "ebur128", "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = ffmpeg_call.communicate()
    file_stats_one_line = (stderr.decode("utf-8"))
    ffmpeg_stats = (file_stats_one_line.splitlines())
    lufs_filehandle = statspath + snd_file_no_ext + ".lufs"
    lufs_file = open(lufs_filehandle, "w") # create the output file as filepath but change extension to .lufs
    lufs_file.write(str(ffmpeg_stats))
    lufs_file.close


if __name__== "__main__":
    main()

    '''NOTES
    Note that SoX and ffmpeg text output  is sent to StdErr, not StdOut.
    in addition, the standard error output is decoded as UTF-8, 
    or there will be a leading 'b' character before the first quoted item in the list.
    
    
    '''