from contextlib import closing

import modules.scripts
from modules import processing
from modules.generation_parameters_copypaste import create_override_settings_dict
from modules.shared import opts
import modules.shared as shared
from modules.ui import plaintext_to_html
import gradio as gr

def add_watermark(image):
    # Convert image to RGB mode to ensure compatibility
    image = image.convert("RGB")

    # Set RGB scale for the new color
    new_color = (147, 147, 147)

    # Get the size of the image
    width, height = image.size

    # Change the color of the top left pixel
    image.putpixel((0, 0), new_color)

    # Change the color of the bottom right pixel
    image.putpixel((width - 1, height - 1), new_color)

    return image

def txt2img(id_task: str, prompt: str, negative_prompt: str, prompt_styles, steps: int, sampler_name: str, n_iter: int, batch_size: int, cfg_scale: float, height: int, width: int, enable_hr: bool, denoising_strength: float, hr_scale: float, hr_upscaler: str, hr_second_pass_steps: int, hr_resize_x: int, hr_resize_y: int, hr_checkpoint_name: str, hr_sampler_name: str, hr_prompt: str, hr_negative_prompt, override_settings_texts, request: gr.Request, *args):
    override_settings = create_override_settings_dict(override_settings_texts)

    p = processing.StableDiffusionProcessingTxt2Img(
        sd_model=shared.sd_model,
        outpath_samples=opts.outdir_samples or opts.outdir_txt2img_samples,
        outpath_grids=opts.outdir_grids or opts.outdir_txt2img_grids,
        prompt=prompt,
        styles=prompt_styles,
        negative_prompt=negative_prompt,
        sampler_name=sampler_name,
        batch_size=batch_size,
        n_iter=n_iter,
        steps=steps,
        cfg_scale=cfg_scale,
        width=width,
        height=height,
        enable_hr=enable_hr,
        denoising_strength=denoising_strength if enable_hr else None,
        hr_scale=hr_scale,
        hr_upscaler=hr_upscaler,
        hr_second_pass_steps=hr_second_pass_steps,
        hr_resize_x=hr_resize_x,
        hr_resize_y=hr_resize_y,
        hr_checkpoint_name=None if hr_checkpoint_name == 'Use same checkpoint' else hr_checkpoint_name,
        hr_sampler_name=None if hr_sampler_name == 'Use same sampler' else hr_sampler_name,
        hr_prompt=hr_prompt,
        hr_negative_prompt=hr_negative_prompt,
        override_settings=override_settings,
    )

    p.scripts = modules.scripts.scripts_txt2img
    p.script_args = args

    p.user = request.username

    if shared.opts.enable_console_prompts:
        print(f"\ntxt2img: {prompt}", file=shared.progress_print_out)

    with closing(p):
        processed = modules.scripts.scripts_txt2img.run(p, *args)

    if processed is None:
        processed = processing.process_images(p)

    # Call add_watermark function on the generated images
    processed_images_with_watermark = [add_watermark(img) for img in processed.images]

    shared.total_tqdm.clear()

    generation_info_js = processed.js()
    if opts.samples_log_stdout:
        print(generation_info_js)

    if opts.do_not_show_images:
        processed.images = []

    # Return processed images with watermark
    return processed_images_with_watermark, generation_info_js, plaintext_to_html(processed.info), plaintext_to_html(processed.comments, classname="comments")

