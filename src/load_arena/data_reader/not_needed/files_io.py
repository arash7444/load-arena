import numpy as np
import pandas as pd
import os


# --------------------------------------------------------------------------------}
# --- OUT FILE
# --------------------------------------------------------------------------------{
class FLEXOutFile:
    def __init__(self, filename):
        self.filename = filename
        self._read()

    def _read(self):
        # --- First read the binary file
        dtype = np.float32  # Flex internal data is stored in single precision
        try:
            self.data, self.tmin, self.dt, self.Version, self.DateID, self.title = (
                read_flex_res(self.filename, dtype=dtype)
            )
        except Exception as e:
            print("FLEX File {}: ".format(self.filename) + "\n" + e.args[0])

        self.nt = np.size(self.data, 0)
        self.nSensors = np.size(self.data, 1)
        self.time = (
            np.arange(self.tmin, self.tmin + self.nt * self.dt, self.dt)
            .reshape(self.nt, 1)
            .astype(dtype)
        )

        # --- Then the sensor file
        sensor_filename = os.path.join(os.path.dirname(self.filename), "sensor")
        if not os.path.isfile(sensor_filename):
            # we are being nice and create some fake sensors info
            self.sensors = read_flex_sensor_fake(self.nSensors)
        else:
            self.sensors = read_flex_sensor(sensor_filename)
            if len(self.sensors["ID"]) != self.nSensors:
                raise ValueError(
                    "Inconsistent number of sensors: {} (sensor file) {} (out file), for file: {}".format(
                        len(self.sensors["ID"]), self.nSensors, self.filename
                    )
                )

    # def _write(self): # TODO
    #    pass

    def __repr__(self):
        return "Flex Out File: {}\nVersion:{} - DateID:{} - Title:{}\nSize:{}x{} - tmin:{} - dt:{}]\nSensors:{}".format(
            self.filename,
            self.Version,
            self.DateID,
            self.title,
            self.nt,
            self.nSensors,
            self.tmin,
            self.dt,
            self.sensors["Name"],
        )

    def _toDataFrame(self):
        # Appending time to form the dataframe
        names = ["Time"] + self.sensors["Name"]
        units = ["s"] + self.sensors["Unit"]
        units = [
            u.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
            for u in units
        ]
        data = np.concatenate((self.time, self.data), axis=1)
        cols = [n + "_[" + u + "]" for n, u in zip(names, units)]
        return pd.DataFrame(data=data, columns=cols)


# --------------------------------------------------------------------------------}
# --- Helper Functions
# --------------------------------------------------------------------------------{
def read_flex_res(filename, dtype=np.float32):
    # Read flex file
    with open(filename, "rb") as fid:
        # _ = struct.unpack('i', fid.read(4)) # Dummy
        _ = np.fromfile(fid, "int32", 1)  # Dummy
        # --- Trying to get DateID
        fid.seek(4)  #
        DateID = np.fromfile(fid, "int32", 6)
        if DateID[0] < 32 and DateID[1] < 13 and DateID[3] < 25 and DateID[4] < 61:
            # OK, DateID was present
            title = fid.read(40).strip()
        else:
            fid.seek(4)  #
            DateID = np.fromfile(fid, "int32", 1)
            title = fid.read(60).strip()
        _ = np.fromfile(fid, "int32", 2)  # Dummy
        # FILE POSITION <<< fid.seek(4 * 19)
        nSensors = np.fromfile(fid, "int32", 1)[0]
        IDs = np.fromfile(fid, "int32", nSensors)
        _ = np.fromfile(fid, "int32", 1)  # Dummy
        # FILE POSITION <<< fid.seek(4*nSensors+4*21)
        Version = np.fromfile(fid, "int32", 1)[0]
        # FILE POSITION <<< fid.seek(4*(nSensors)+4*22)
        if Version == 12:
            raise NotImplementedError(
                "Flex out file with version 12, TODO. Implement it!"
            )
            # TODO
            # fseek(o.fid,4*(21+o.nSensors),-1);% seek to the data from beginning of file
            # RL=o.nSensors+5; % calculate the length of each row
            # A = fread(o.fid,[RL,inf],'single'); % read whole file
            # t=A(2,:);% time vector contained in row 2
            # o.SensorData=A(5:end,:);
            # save relevant information
            # o.tmin = t(1)     ;
            # o.dt   = t(2)-t(1);
            # o.t    = t        ;
            # o.nt   = length(t);
        elif Version in [0, 2, 3]:
            tmin = np.fromfile(fid, "f", 1)[0]  # Dummy
            dt = np.fromfile(fid, "f", 1)[0]  # Dummy
            scale_factors = np.fromfile(fid, "f", nSensors).astype(dtype)
        # --- Reading Time series
        # FILE POSITION <<< fid.seek(8*nSensors + 48*2)
        data = np.fromfile(fid, "int16").astype(
            dtype
        )  # data = np.fromstring(fid.read(), 'int16').astype(dtype)
        nt = int(len(data) / nSensors)
        try:
            if Version == 3:
                data = data.reshape(nSensors, nt).transpose()
            else:
                data = data.reshape(nt, nSensors)
        except ValueError:
            raise ValueError(
                "Flat data length {} is not compatible with {}x{} (nt x nSensors)".format(
                    len(data), nt, nSensors
                )
            )
        for i in range(nSensors):
            data[:, i] *= scale_factors[i]

        return (data, tmin, dt, Version, DateID, title)


def read_flex_sensor(sensor_file):
    with open(sensor_file, encoding="utf-8") as fid:
        sensor_info_lines = fid.readlines()[2:]
    sensor_info = []
    d = dict(
        {"ID": [], "Gain": [], "Offset": [], "Unit": [], "Name": [], "Description": []}
    )
    for line in sensor_info_lines:
        line = line.strip().split()
        d["ID"].append(int(line[0]))
        d["Gain"].append(float(line[1]))
        d["Offset"].append(float(line[2]))
        d["Unit"].append(line[5])
        d["Name"].append(line[6])
        d["Description"].append(" ".join(line[7:]))
    return d


def read_flex_sensor_fake(nSensors):
    d = dict(
        {"ID": [], "Gain": [], "Offset": [], "Unit": [], "Name": [], "Description": []}
    )
    for i in range(nSensors):
        d["ID"].append(i + 1)
        d["Gain"].append(1.0)
        d["Offset"].append(0.0)
        d["Unit"].append("(NA)")
        d["Name"].append("S{:04d}".format(i + 1))
        d["Description"].append("NA")
    return d


# # Minimal compatibility wrapper for existing hawc2_reader usage
# class ReadHawc2:
#     """Lightweight wrapper around FLEXOutFile to provide the
#     minimal interface expected by `hawc2_reader.py`.

#     Methods provided:
#     - ReadAll(): returns the time-series data as a NumPy array (nt x nSensors)
#     - ReadFLEX(): alias for ReadAll()

#     Attributes provided:
#     - ChInfo: list where index 0 is the list of sensor names
#     - t: 1D NumPy array with time values
#     """

#     def __init__(self, filename):
#         # accept pathlib.Path or string
#         self.filename = str(filename)
#         self._out = FLEXOutFile(self.filename)
#         # ChInfo[0] should match earlier code expecting sensor names
#         self.ChInfo = [self._out.sensors.get("Name", [])]
#         # time vector (flattened)
#         try:
#             self.t = self._out.time.flatten()
#         except Exception:
#             # fallback: construct from tmin/dt/nt if available
#             try:
#                 self.t = (
#                     np.arange(
#                         self._out.tmin,
#                         self._out.tmin + self._out.nt * self._out.dt,
#                         self._out.dt,
#                     )
#                 ).astype(self._out.data.dtype)
#             except Exception:
#                 self.t = np.array([])

#     def ReadAll(self):
#         return self._out.data

#     def ReadFLEX(self):
#         return self.ReadAll()
