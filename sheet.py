import sys
import cv2
import numpy as np
import yt_dlp
import os

def calculate_similarity(frame1, frame2):
    # Convert frames to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Ensure both images have the same size
    if gray1.shape != gray2.shape:
        height, width = gray1.shape
        gray2 = cv2.resize(gray2, (width, height))
    
    # Calculate structural similarity index
    similarity = cv2.compareHist(gray1, gray2, cv2.HISTCMP_CORREL)
    
    return similarity

def universal(video_url, variance=False, skip=None, path=None, multipage=True):
    name = video_url
    if name[-1] == '/':
        name = name[:-1]
    name = name.split('/')[-1]

    ydl_opts = {
        'outtmpl': '/tmp/%(title)s.%(ext)s'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        tmp_path = ydl.prepare_filename(info_dict)
        ydl.download([video_url])

    # Continue with the rest of the code
    cap = cv2.VideoCapture(tmp_path)

    img = None
    result = None
    frame_number = 0
    img_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        frame_number += 1
        if frame is None or not ret:
            break

        if skip is not None and frame_number < skip:
            continue

        if frame_number % 120 != 0:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate the mean for each horizontal line
        line_means = np.mean(gray, axis=1) if not variance else np.var(gray, axis=1)

        # Apply convolution on the line means using a kernel size of 10
        kernel_size = 40
        line_means_original = line_means
        line_means = np.convolve(line_means, np.ones(kernel_size)/kernel_size, mode='same')

        threshold = 50
        padding = 150
        padding2 = 30
        
        # Find the abrupt point where the line_means value steeps and not within the padding areas on both sides
        abrupt_point = [0, 0]
        for i in range(padding, len(line_means) - padding):
            pos_diff = line_means[i] - line_means[i-kernel_size]
            neg_diff = line_means[i] - line_means[i+kernel_size]
            max_diff = max(abs(pos_diff), abs(neg_diff))
            if max_diff > abrupt_point[0]:
                if abs(pos_diff) > abs(neg_diff):
                    abrupt_point = [max_diff, i - int(kernel_size * 0.5)]
                else:
                    abrupt_point = [max_diff, i + int(kernel_size * 0.5)]

        abrupt_point = abrupt_point[1] if abrupt_point[0] > threshold else None

        
        # Find the exact border by searching from the abrupt_point in line_means_original
        if abrupt_point is None:
            continue

        found_exact = False
        abrupt_point_r = abrupt_point
        for i in range(abrupt_point, abrupt_point + int(kernel_size / 2)):
            if abs(line_means_original[i] - line_means_original[abrupt_point]) > threshold:
                abrupt_point = i
                found_exact = True
                break
        if not found_exact:
            for i in range(abrupt_point, abrupt_point - int(kernel_size / 2), -1):
                if abs(line_means_original[i] - line_means_original[abrupt_point]) > threshold:
                    found_exact = True
                    abrupt_point = i
                    break
        if not found_exact:
            abrupt_point = abrupt_point_r
        
        smaller_frame = None
        if abrupt_point < (frame.shape[0] / 2):
            smaller_frame = frame[padding2:abrupt_point]
        else:
            smaller_frame = frame[abrupt_point:-(padding2 + 1)]

        if img is None:
            img = smaller_frame
            result = smaller_frame

        if smaller_frame is not None:
        # Compare the smaller_frame and img using a similarity metric
            similarity_threshold = 0.9  # Adjust the threshold as needed
            similarity = calculate_similarity(smaller_frame, img)

            if similarity < similarity_threshold:
                if multipage and result.shape[0] > (result.shape[1] * 10 / 9):
                    # Save the current image
                    if path is None:
                        write = name + f'sheet-{str(img_number)}.png'
                    else:
                        write = os.path.join(path, f'{str(img_number)}.png')
                    cv2.imwrite(write, result)
                    # Start a new image
                    result = smaller_frame
                    img = smaller_frame
                    img_number += 1
                else:
                    result = np.vstack((result, smaller_frame))
                    img = smaller_frame

    cap.release()

    if path is None:
        write = name + f'sheet-{img_number}.png'
    else:
        write = os.path.join(path, f'{img_number}.png')
    cv2.imwrite(write, result)
    os.remove(tmp_path)

def color_variance(video_url, skip=None, path=None, multipage=True):
    name = video_url
    if name[-1] == '/':
        name = name[:-1]
    name = name.split('/')[-1]

    ydl_opts = {
        'outtmpl': '/tmp/%(title)s.%(ext)s'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        tmp_path = ydl.prepare_filename(info_dict)
        ydl.download([video_url])

    # Continue with the rest of the code
    cap = cv2.VideoCapture(tmp_path)

    img = None
    result = None
    frame_number = 0
    img_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        frame_number += 1
        if frame is None or not ret:
            break

        if skip is not None and frame_number < skip:
            continue

        if frame_number % 120 != 0:
            continue

        # Calculate the variance of the RGB channels
        variance = np.var(frame, axis=(2))

        # Calculate the mean for each horizontal line
        line_means = np.mean(variance, axis=1)
        # conv by 20
        line_means = np.convolve(line_means, np.ones(20)/20, mode='valid')

        # Find a lower gate that at least 200 points in mean_lines are lower than the gate
        lower_gate = np.percentile(line_means, 15)  # Set the initial gate as the 75th percentile of line_means

        lower_gate += 30

        # find the points where the line_means are lower than the lower_gate
        points = np.where(line_means < lower_gate)[0]

        # Form a range by clustering the points by distance
        distance_tolerance = 100  # Adjust the tolerance as needed
        clusters = []
        current_cluster = []
        for i in range(len(points)-1):
            current_cluster.append(points[i])
            if points[i+1] - points[i] > distance_tolerance:
                clusters.append(current_cluster)
                current_cluster = []
        # Add the last point to the last cluster
        current_cluster.append(points[-1])
        clusters.append(current_cluster)

        # Find the cluster with the maximum number of points
        max_cluster = max(clusters, key=len)

        # Find the boundary of the range
        boundary = (max_cluster[0], max_cluster[-1]+1)

        smaller_frame = frame[boundary[0]:boundary[1]]


        if img is None:
            img = smaller_frame
            result = smaller_frame

        if smaller_frame is not None:
        # Compare the smaller_frame and img using a similarity metric
            similarity_threshold = 0.9  # Adjust the threshold as needed
            similarity = calculate_similarity(smaller_frame, img)

            if similarity < similarity_threshold:
                if multipage and result.shape[0] > (result.shape[1] * 10 / 9):
                    print(result.shape[0], result.shape[1], 'over')
                    # Save the current image
                    if path is None:
                        write = name + f'sheet-{str(img_number)}.png'
                    else:
                        write = os.path.join(path, f'{str(img_number)}.png')
                    cv2.imwrite(write, result)
                    # Start a new image
                    result = smaller_frame
                    img = smaller_frame
                    img_number += 1
                else:
                    result = np.vstack((result, smaller_frame))
                    img = smaller_frame

    cap.release()

    if path is None:
        write = name + f'sheet-{img_number}.png'
    else:
        write = os.path.join(path, f'{img_number}.png')

    cv2.imwrite(write, result)
    os.remove(tmp_path)


if __name__ == '__main__':
    video_url = input('Enter the video URL: ')
    print('Select the mode:')
    print('1. Mean')
    print('2. Variance')
    print('3. Color Variance')
    mode = input('Enter the mode (colour variance by default): ')
    if mode == '':
        mode = '3'
    skip = input('Enter the frame number to skip (Enter to ignore): ')
    if skip == '':
        skip = None
    else:
        skip = int(skip)
    if mode == '1':
        universal(video_url, variance=False, skip=skip)
    elif mode == '2':
        universal(video_url, variance=True, skip=skip)
    elif mode == '3':
        color_variance(video_url, skip=skip)
    else:
        print('Invalid mode')
