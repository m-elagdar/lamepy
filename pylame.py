#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# https://github.com/gypified/libmp3lame/blob/master/API
# https://bikulov.org/blog/2013/10/01/using-cuda-c-functions-in-python-via-.so-and-ctypes/

from ctypes import cdll, c_char, Structure, POINTER, c_short, c_void_p, pointer, c_int, c_ulong, c_ubyte
import numpy as np
import sys, os
import psutil

def mp3_write(file, data, samplerate):
    lame = cdll.LoadLibrary("libmp3lame.so")
    c = cdll.LoadLibrary("libc.so.6")
    lame.get_lame_version.restype = POINTER(c_char*10)
    ret_code = lame.get_lame_version()
    #print("lame v%s"%(ret_code.contents.value.decode("utf-8")))
    
    data = data.squeeze()
    channels = data.ndim
    lame.lame_init.restype = POINTER(type("lame_global_flags", (Structure,), {}))
    gfp = lame.lame_init()
    lame.lame_set_num_channels(gfp, channels)
    lame.lame_set_in_samplerate(gfp, samplerate)

    #lame.lame_set_bWriteVbrTag(gfp, 0)

    ret_code = lame.lame_init_params(gfp)
    if ret_code!=0: raise ValueError("couldn't initialize lame. return code: %d"%(ret_code))

    d = data
    i16 = np.iinfo(np.int16); d = np.clip(d*i16.max, i16.min, i16.max).astype(np.int16)
    wav_size = int(round(1.25*len(d)*channels + 7200))
    mp3buffer = np.zeros(wav_size, np.ubyte)
    mbp = mp3buffer.ctypes.data_as(POINTER(c_short))

    if channels==1: pcm = pcm_r = d.ctypes.data_as(POINTER(c_short))
    else: dC = np.array(d, order="F"); pcm, pcm_r = (x.ctypes.data_as(POINTER(c_short)) for x in (dC[:, 0], dC[:, 1]))

    ret_code = lame.lame_encode_buffer(gfp, pcm, pcm_r, len(d), mbp, mp3buffer.nbytes)
    if ret_code<0: raise ValueError("couldn't encode mp3. return code: %d"%(ret_code))
    #print(ret_code)
    
    written_vals = int(ret_code/mp3buffer.itemsize)
    mbp_now = mp3buffer[written_vals:].ctypes.data_as(POINTER(c_short))
    ret_code = lame.lame_encode_flush(gfp, mbp_now, mp3buffer.nbytes-ret_code)
    if ret_code<0: raise ValueError("couldn't encode mp3. return code: %d"%(ret_code))
    #print(ret_code)
    out_d = mp3buffer[:written_vals+int(ret_code/mp3buffer.itemsize)]

    # https://ctypes-users.narkive.com/AMetiCGf/can-ctypes-type-a-pointer-to-opaque-structure
    # Example: x = c.fopen(b"c.mp3", b"wb"); c.fprintf(x, b"test"); c.fclose(x)
    c.fopen.restype = POINTER(type("FILE", (Structure,), {}))
    fd = c.fopen(file.encode("utf-8"), b"wb+")
    c.fwrite(mbp, mp3buffer.itemsize, len(out_d), fd)
    lame.lame_mp3_tags_fid(gfp, fd)
    lame.lame_close(gfp)
    c.fclose(fd)

def mp3_read(file):
    lame = cdll.LoadLibrary("libmp3lame.so")
    lame.hip_decode_init.restype = POINTER(type("hip_global_flags", (Structure,), {}))
    gfp = lame.hip_decode_init()

    mp3buffer = np.fromfile(file, dtype=np.ubyte)
    mbp = mp3buffer.ctypes.data_as(POINTER(c_ubyte))
    mp3_size = len(mp3buffer)*mp3buffer.itemsize

    pcm = pcm_r = pointer((c_short*0)())

    headers = mp3data_struct()
    ret_code = lame.hip_decode_headers(gfp, mbp, mp3_size, pcm, pcm_r, pointer(headers))
    if not headers.header_parsed: ret_code = lame.hip_decode_headers(gfp, mbp, mp3_size, pcm, pcm_r, pointer(headers))
    channels = headers.stereo

    nbytes = min(round(mp3_size*100 + 7200), int(psutil.virtual_memory().available*0.9))
    pcmbuffer = np.zeros(nbytes, np.int8)
    pcm = pcmbuffer.ctypes.data_as(POINTER(c_short))
    if channels==2:
        pcmbuffer_r = np.zeros(nbytes, np.int8)
        pcm_r = pcmbuffer_r.ctypes.data_as(POINTER(c_short))
    ret_code = lame.hip_decode_headers(gfp, mbp, mp3_size, pcm, pcm_r, pointer(headers))
    
    nbytes = (headers.nsamp*2) or int(ret_code/pcmbuffer.itemsize) #*2 because of int16
    if ret_code<0: raise ValueError("couldn't decode mp3. return code: %d"%(ret_code))
    #print(ret_code)
    #ret_code = lame.hip_decode(gfp, mbp, mp3_size, pcm, pcm_r)
    out_d = pcmbuffer[:nbytes].copy()
    del pcmbuffer
    out_d = np.frombuffer(out_d.tobytes(), np.int16)
    if channels==2:
        out_d_r = pcmbuffer_r[:nbytes].copy()
        del pcmbuffer_r
        out_d_r = np.frombuffer(out_d_r.tobytes(), np.int16)
        out_d = np.stack((out_d, out_d_r), 1)
    out_d = np.clip(out_d/np.iinfo(np.int16).max, -1, 1).astype(np.float32)
    ret_code = lame.hip_decode_exit(gfp)
    return out_d, headers.samplerate

class mp3data_struct(Structure):
    _fields_ = [
      ("header_parsed", c_int),
      ("stereo", c_int),          #/* number of channels                             */
      ("samplerate", c_int),      #/* sample rate                                    */
      ("bitrate", c_int),         #/* bitrate                                        */
      ("mode", c_int),
      ("mode_ext", c_int),
      ("framesize", c_int),       #/* number of samples per mp3 frame                */

      #/* this data is only computed if mpglib detects a Xing VBR header */
      ("nsamp", c_ulong), #/* number of samples in mp3 file.                 */
      ("totalframes", c_int),     #/* total number of frames in mp3 file             */
      #/* this data is not currently computed by the mpglib routines */
      ("framenum", c_int),
    ]

if __name__ == "__main__":
    import soundfile as sf
    args = iter(sys.argv[1:])
    in_file= next(args, "in.wav")
    mode = os.path.splitext(in_file)[1]
    if mode==".mp3":
        out_file = next(args, in_file+".wav")
        d, r = mp3_read(in_file)
        print("read mp3")
        sf.write(out_file, d, r)
        print("wrote wav")
    elif mode==".wav":
        out_file = next(args, in_file+".mp3")
        d, r = sf.read(in_file)
        print("read wav")
        mp3_write(out_file, d, r)
        print("wrote mp3")
    else: raise ValueError("Unsupported mode: {}".format(mode))
