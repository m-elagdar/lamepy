# pylame
A Python wrapper for [LAME](https://lame.sourceforge.io/)

## Usage
1. Install [LAME](https://lame.sourceforge.io/)
    1. For Ubuntu: `sudo apt install libmp3lame-dev`
1. (Option 1) Call from command line
    ```bash
    ./pylame.py in.wav out.mp3
    ./pylame.py in.mp3 out.wav
    ```
2. (Option 2) Use pylame in a script
    ```python
    from pylame import mp3_read, mp3_write
    import soundfile as sf

    # read a file
    in_file = "in.wav"
    out_file = "out.mp3"
    out_wav_file = "out.wav"

    # read a wav
    d, r = sf.read(in_file)

    # write to mp3
    mp3_write(out_file, d, r)

    # read an mp3
    d, r = mp3_read(out_file)

    # write to a wav
    sf.write(out_wav_file, d, r)
    ```

## Known issues
#### Single channel .mp3
1. Single channel .mp3 are written without duration in their header
