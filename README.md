# lamepy
A Python wrapper for [LAME](https://lame.sourceforge.io/). It can encode and decode .mp3 audio files

## Environment
1. Install [LAME](https://lame.sourceforge.io/)
    1. For Ubuntu: `sudo apt install libmp3lame-dev`
1. Intall Python requirements
    ```
    # Install pip if not installed
    wget https://bootstrap.pypa.io/get-pip.py -O - | python3
    # Then install requirements
    python3 -m pip install -r requirements.txt
    ```

## Usage
1. (Option 1) Call from command line
    ```bash
    python3 ./lamepy.py in.wav out.mp3
    python3 ./lamepy.py in.mp3 out.wav
    ```
2. (Option 2) Use lamepy in a script
    ```python
    from lamepy import mp3_read, mp3_write
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
