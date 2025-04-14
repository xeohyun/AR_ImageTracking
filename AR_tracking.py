import numpy as np
import cv2 as cv

input_file = 'AR.MOV'
K = np.array([
    [881.83077103,    0.0,           957.47800829],
    [0.0,            886.33664607,   533.66150692],
    [0.0,              0.0,             1.0]
])
dist_coeff = np.array([
    0.00658917,    
   -0.00147395,    
   -0.00024292,    
    0.00232185,    
    0.00168796     
])

board_pattern = (8,6)
board_cellsize = 0.025
board_criteria = cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_NORMALIZE_IMAGE + cv.CALIB_CB_FAST_CHECK

# Open a video
video = cv.VideoCapture(input_file)
assert video.isOpened(), 'Cannot read the given input, ' + input_file

theta = np.linspace(0, 4 * np.pi, 100)
r = board_cellsize * 0.5
z = np.linspace(0, board_cellsize * 7, 100)

helix1 = np.array([r*np.cos(theta), r*np.sin(theta), -z]).T
helix2 = np.array([-r*np.cos(theta), -r*np.sin(theta), -z]).T

# 중앙 정렬
center_offset = np.array([5 * board_cellsize, 3.5 * board_cellsize, 0])
helix1 += center_offset
helix2 += center_offset

# Prepare 3D points on a chessboard
obj_points = board_cellsize * np.array([[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])])

# Run pose estimation
while True:
    # Read an image from the video
    valid, img = video.read()
    if not valid:
        break

    # Estimate the camera pose
    complete, img_points = cv.findChessboardCorners(img, board_pattern, board_criteria)
    if complete:
        ret, rvec, tvec = cv.solvePnP(obj_points, img_points, K, dist_coeff)

        # Draw the box on the image
        line_lower, _ = cv.projectPoints(helix1, rvec, tvec, K, dist_coeff)
        line_upper, _ = cv.projectPoints(helix2, rvec, tvec, K, dist_coeff)
        cv.polylines(img, [np.int32(line_lower)], True, (255, 0, 0), 2)
        cv.polylines(img, [np.int32(line_upper)], True, (0, 0, 255), 2)
        for b, t in zip(line_lower, line_upper):
            cv.line(img, np.int32(b.flatten()), np.int32(t.flatten()), (0, 255, 0), 2)

        # Print the camera position
        R, _ = cv.Rodrigues(rvec) # Alternative) scipy.spatial.transform.Rotation
        p = (-R.T @ tvec).flatten()
        info = f'XYZ: [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}]'
        cv.putText(img, info, (10, 25), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0))

    # Show the image and process the key event
    cv.imshow('Pose Estimation (Chessboard)', img)
    key = cv.waitKey(10)
    if key == ord(' '):
        key = cv.waitKey()
    if key == 27: # ESC
        break

video.release()
cv.destroyAllWindows()