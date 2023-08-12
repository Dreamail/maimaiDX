import os
import traceback
from io import BytesIO
from typing import Union

from PIL import Image, ImageDraw

from nonebot.adapters.onebot.v11 import MessageSegment

from .. import (
    BOTNAME,
    SIYUAN,
    TBFONT,
    category,
    coverdir,
    levelList,
    maimaidir,
    plate_to_version,
    ratingdir,
)
from .image import DrawText, image_to_base64
from .maimai_best_50 import *
from .maimaidx_api_data import *
from .maimaidx_music import Music, RaMusic, download_music_pictrue, mai


async def draw_music_info_to_message_segment(music: Music) -> MessageSegment:
    return MessageSegment.image(await draw_music_info(music))


async def draw_music_info(music: Music) -> BytesIO:
    """
    旧的谱面详情
    """
    im = Image.open(os.path.join(maimaidir, 'music_bg.png')).convert('RGBA')
    genre = Image.open(os.path.join(maimaidir, f'music-{category[music.basic_info.genre]}.png'))
    cover = Image.open(await download_music_pictrue(music.id)).resize((360, 360))
    ver = Image.open(os.path.join(maimaidir, f'{music.type}.png')).resize((94, 35))
    line = Image.new('RGBA', (400, 2), (255, 255, 255, 255))

    im.alpha_composite(genre, (150, 170))
    im.alpha_composite(cover, (170, 260))
    im.alpha_composite(ver, (435, 585))
    im.alpha_composite(line, (150, 710))

    dr = ImageDraw.Draw(im)
    tb = DrawText(dr, TBFONT)
    sy = DrawText(dr, SIYUAN)

    tb.draw(200, 195, 24, music.id, anchor='mm')
    sy.draw(410, 195, 22, music.basic_info.genre, anchor='mm')
    sy.draw_partial_opacity(350, 660, 30, music.title, 1, anchor='mm')
    sy.draw_partial_opacity(350, 690, 12, music.basic_info.artist, 1, anchor='mm')
    sy.draw_partial_opacity(150, 725, 15, f'Version: {music.basic_info.version}', 1, anchor='lm')
    sy.draw_partial_opacity(550, 725, 15, f'BPM: {music.basic_info.bpm}', 1, anchor='rm')
    for n, i in enumerate(list(map(str, music.ds))):
        if n == 4:
            color = (195, 70, 231, 255)
        else:
            color = (255, 255, 255, 255)
        tb.draw(160 + 95 * n, 814, 25, i, color, 'mm')
    sy.draw(350, 980, 14, f'Designed by Yuri-YuzuChaN | Generated by {BOTNAME} BOT', (255, 255, 255, 255), 'mm', 1, (159, 81, 220, 255))

    bio = BytesIO()
    im.save(bio, format='PNG')
    bio.seek(0)
    return bio


async def music_play_data(payload: dict, songs: str) -> Union[str, MessageSegment]:
    payload['version'] = list(set(version for version in plate_to_version.values()))
    data = await get_player_data('plate', payload)
    if isinstance(data, str):
        return data

    player_data: list[dict[str, Union[float, str, int]]] = []
    for i in data['verlist']:
        if i['id'] == int(songs):
            player_data.append(i)
    if not player_data:
        return '您未游玩该曲目'
    
    player_data.sort(key=lambda a: a['level_index'])
    music = mai.total_list.by_id(songs)

    im = Image.open(os.path.join(maimaidir, 'info_bg.png')).convert('RGBA')
    genre = Image.open(os.path.join(maimaidir, f'info-{category[music.basic_info.genre]}.png'))
    cover = Image.open(await download_music_pictrue(music.id)).resize((210, 210))
    version = Image.open(os.path.join(maimaidir, f'{music.type}.png')).resize((108, 40))

    dr = ImageDraw.Draw(im)
    tb = DrawText(dr, TBFONT)
    sy = DrawText(dr, SIYUAN)

    im.alpha_composite(genre, (45, 145))
    im.alpha_composite(cover, (69, 184))
    im.alpha_composite(version, (725, 360))

    tb.draw(430, 167, 20, music.id, anchor='mm')
    sy.draw(610, 167, 20, music.basic_info.genre, anchor='mm')
    sy.draw(295, 225, 30, music.title, anchor='lm')
    sy.draw(295, 260, 15, f'Artist: {music.basic_info.artist}', anchor='lm')
    sy.draw(295, 310, 15, f'BPM: {music.basic_info.bpm}', anchor='lm')
    sy.draw(295, 330, 15, f'Version: {music.basic_info.version}', anchor='lm')

    y = 120
    TEXT_COLOR = [(14, 117, 54, 255), (199, 69, 12, 255), (175, 0, 50, 255), (103, 20, 141, 255), (103, 20, 141, 255)]
    for _data in player_data:
        ds: float = music.ds[_data['level_index']]
        lv: int = _data['level_index']
        ra, rate = computeRa(ds, _data['achievements'], israte=True)

        rank = Image.open(os.path.join(maimaidir, f'UI_TTR_Rank_{rate}.png')).resize((120, 57))
        im.alpha_composite(rank, (430, 515 + y * lv))
        if _data['fc']:
            fcl = {'fc': 'FC', 'fcp': 'FCp', 'ap': 'AP', 'app': 'APp'}
            fc = Image.open(os.path.join(maimaidir, f'UI_CHR_PlayBonus_{fcl[_data["fc"]]}.png')).resize((76, 76))
            im.alpha_composite(fc, (575, 511 + y * lv))
        if _data['fs']:
            fsl = {'fs': 'FS', 'fsp': 'FSp', 'fsd': 'FSD', 'fsdp': 'FSDp'}
            fs = Image.open(os.path.join(maimaidir, f'UI_CHR_PlayBonus_{fsl[_data["fs"]]}.png')).resize((76, 76))
            im.alpha_composite(fs, (650, 511 + y * lv))

        p, s = f'{_data["achievements"]:.4f}'.split('.')
        r = tb.get_box(p, 36)
        tb.draw(90, 545 + y * lv, 30, ds, anchor='mm')
        tb.draw(200, 567 + y * lv, 36, p, TEXT_COLOR[lv], 'ld')
        tb.draw(200 + r[2], 565 + y * lv, 30, f'.{s}%', TEXT_COLOR[lv], 'ld')
        tb.draw(790, 545 + y * lv, 30, ra, TEXT_COLOR[lv], 'mm')

    sy.draw(450, 1180, 20, f'Designed by Yuri-YuzuChaN | Generated by {BOTNAME} BOT', (159, 81, 220, 255), 'mm', 2, (255, 255, 255, 255))
    msg = MessageSegment.image(image_to_base64(im))

    return msg


async def music_play_data_dev(payload: dict, songs: str) -> Union[str, MessageSegment]:

    data = await get_dev_player_data(payload)

    if isinstance(data, str):
        return data
    datalist = data['records'] if token else data['verlist']
    player_data: list[dict[str, Union[float, str, int]]] = []
    for i in datalist:
        if i['song_id'] == int(songs):
            player_data.append(i)
    if not player_data:
        return '您未游玩该曲目'
    
    DXSTAR_DEST = [0, 540, 530, 520, 510, 500]

    player_data.sort(key=lambda a: a['level_index'])
    music = mai.total_list.by_id(songs)

    bg = os.path.join(maimaidir, 'info_bg_2.png')
    im = Image.open(bg).convert('RGBA')
    genre = Image.open(os.path.join(maimaidir, f'info-{category[music.basic_info.genre]}.png'))
    cover = Image.open(await download_music_pictrue(music.id)).resize((210, 210))
    version = Image.open(os.path.join(maimaidir, f'{music.type}.png')).resize((108, 40))
    dxstar = [Image.open(os.path.join(maimaidir, f'UI_RSL_DXScore_Star_0{_ + 1}.png')).resize((20, 20)) for _ in range(3)]

    dr = ImageDraw.Draw(im)
    tb = DrawText(dr, TBFONT)
    sy = DrawText(dr, SIYUAN)

    im.alpha_composite(genre, (45, 145))
    im.alpha_composite(cover, (69, 184))
    im.alpha_composite(version, (725, 360))

    tb.draw(430, 167, 20, music.id, anchor='mm')
    sy.draw(610, 167, 20, music.basic_info.genre, anchor='mm')
    sy.draw(295, 225, 30, music.title, anchor='lm')
    sy.draw(295, 260, 15, f'Artist: {music.basic_info.artist}', anchor='lm')
    sy.draw(295, 310, 15, f'BPM: {music.basic_info.bpm}', anchor='lm')
    sy.draw(295, 330, 15, f'Version: {music.basic_info.version}', anchor='lm')

    y = 120
    TEXT_COLOR = [(14, 117, 54, 255), (199, 69, 12, 255), (175, 0, 50, 255), (103, 20, 141, 255), (103, 20, 141, 255)]
    for _data in player_data:
        ds: float = _data['ds']
        lv: int = _data['level_index']
        dxscore = _data['dxScore']
        ra, rate = computeRa(ds, _data['achievements'], israte=True)

        rank = Image.open(os.path.join(maimaidir, f'UI_TTR_Rank_{rate}.png')).resize((120, 57))
        im.alpha_composite(rank, (358, 518 + y * lv))

        _dxscore = sum(music.charts[lv].notes) * 3
        diff_sum_dx = dxscore / _dxscore * 100
        dxtype, dxnum = dxScore(diff_sum_dx)
        for _ in range(dxnum):
            im.alpha_composite(dxstar[dxtype], (DXSTAR_DEST[dxnum] + 20 * _, 550 + y * lv))

        if _data['fc']:
            fcl = {'fc': 'FC', 'fcp': 'FCp', 'ap': 'AP', 'app': 'APp'}
            fc = Image.open(os.path.join(maimaidir, f'UI_CHR_PlayBonus_{fcl[_data["fc"]]}.png')).resize((76, 76))
            im.alpha_composite(fc, (605, 511 + y * lv))
        if _data['fs']:
            fsl = {'fs': 'FS', 'fsp': 'FSp', 'fsd': 'FSD', 'fsdp': 'FSDp'}
            fs = Image.open(os.path.join(maimaidir, f'UI_CHR_PlayBonus_{fsl[_data["fs"]]}.png')).resize((76, 76))
            im.alpha_composite(fs, (670, 511 + y * lv))

        p, s = f'{_data["achievements"]:.4f}'.split('.')
        r = tb.get_box(p, 36)
        tb.draw(90, 545 + y * lv, 30, ds, anchor='mm')
        tb.draw(175, 567 + y * lv, 36, p, TEXT_COLOR[lv], 'ld')
        tb.draw(175 + r[2], 565 + y * lv, 30, f'.{s}%', TEXT_COLOR[lv], 'ld')
        tb.draw(550, (535 if dxnum != 0 else 548) + y * lv, 20, f'{dxscore}/{_dxscore}', TEXT_COLOR[lv], 'mm')
        tb.draw(790, 545 + y * lv, 30, ra, TEXT_COLOR[lv], 'mm')

    sy.draw(450, 1180, 20, f'Designed by Yuri-YuzuChaN | Generated by {BOTNAME} BOT', (159, 81, 220, 255), 'mm', 2, (255, 255, 255, 255))
    msg = MessageSegment.image(image_to_base64(im))

    return msg


async def new_draw_music_info(music: Music) -> str:
    """
    新的查看谱面
    """
    im = Image.open(os.path.join(maimaidir, 'song_bg.png')).convert('RGBA')
    dr = ImageDraw.Draw(im)
    tb = DrawText(dr, TBFONT)
    sy = DrawText(dr, SIYUAN)
    
    default_color = (140, 44, 213, 255)
    
    im.alpha_composite(Image.open(await download_music_pictrue(music.id)), (205, 305))
    im.alpha_composite(Image.open(os.path.join(maimaidir, f'{music.basic_info.version}.png')).resize((250, 120)), (1340, 590))
    im.alpha_composite(Image.open(os.path.join(maimaidir, f'{music.type}.png')), ((1150, 643)))
    
    title = music.title
    if coloumWidth(title) > 42:
        title = changeColumnWidth(title, 41) + '...'
    sy.draw(640, 350, 40, title, default_color, 'lm')
    sy.draw(640, 425, 30, music.basic_info.artist, default_color, 'lm')
    tb.draw(705, 548, 40, music.basic_info.bpm, default_color, 'lm')
    tb.draw(640, 665, 40, f'ID {music.id}', default_color, 'lm')
    sy.draw(970, 665, 30, music.basic_info.genre, default_color, 'mm')
    
    for num, _ in enumerate(music.level):
        if num == 4:
            color = default_color
        else:
            color = (255, 255, 255, 255)
        tb.draw(280, 955 + 110 * num, 30, f'{music.level[num]}({music.ds[num]})', color, 'mm')
        tb.draw(475, 945 + 110 * num, 40, f'{round(music.stats[num].fit_diff, 2):.2f}' if music.stats and music.stats[num] else '-', default_color, anchor='mm')
        if num > 1:
            sy.draw(585 + 414 * (num - 2), 1523, 22, music.charts[num].charter, color, 'mm')
        
        notes = list(music.charts[num].notes)
        tb.draw(658, 945 + 110 * num, 40, sum(notes), default_color, 'mm')
        if len(notes) == 4:
            notes.insert(3, 0)
        for n, c in enumerate(notes):
            tb.draw(834 + 175 * n, 945 + 110 * num, 40, c, default_color, 'mm')
    msg = MessageSegment.image(image_to_base64(im))
    
    return msg


def update_rating_table() -> str:
    """
    更新定数表
    """
    try:
        lv1 = ['6', '7', '8', '12', '13']
        lv2 = ['7+', '8+', '9', '9+', '10', '10+', '11', '11+']
        lv3 = ['12+', '13+', '14', '14+', '15']
        
        bg_color = [(111, 212, 61, 255), (248, 183, 9, 255), (255, 129, 141, 255), (159, 81, 220, 255), (219, 170, 255, 255)]
        dx = Image.open(os.path.join(maimaidir, 'DX.png')).convert('RGBA').resize((44, 16))
        diff = [Image.new('RGBA', (75, 75), color) for color in bg_color]
        
        for ra in levelList[5:]:
            musiclist = mai.total_list.lvList(True)

            if ra in lv1:
                im = Image.open(os.path.join(ratingdir, 'Rating3.png')).convert('RGBA')
            elif ra in lv2:
                im = Image.open(os.path.join(ratingdir, 'Rating2.png')).convert('RGBA')
            elif ra in lv3:
                im = Image.open(os.path.join(ratingdir, 'Rating.png')).convert('RGBA')
            dr = ImageDraw.Draw(im)
            sy = DrawText(dr, SIYUAN)

            if ra in levelList[-3:]:
                bg = os.path.join(ratingdir, '14.png')
                ralist = levelList[-3:]
            else:
                bg = os.path.join(ratingdir, f'{ra}.png')
                ralist = [ra]

            lvlist: Dict[str, List[RaMusic]] = {}
            for lvs in list(reversed(ralist)):
                for _ra in musiclist[lvs]:
                    lvlist[_ra] = musiclist[lvs][_ra]

            if ra in ['14', '14+', '15']:
                lvtext = 'Level.14 - 15   定数表'
            else:
                lvtext = f'Level.{ra}   定数表'

            sy.draw(750, 120, 65, lvtext, (0, 0, 0, 255), 'mm')
            y = 120
            for lv in lvlist:
                y += 10
                sy.draw(100, y + 120, 50, lv, (0, 0, 0, 255), 'mm')
                for num, music in enumerate(lvlist[lv]):
                    if num % 15 == 0:
                        x = 200
                        y += 85
                    else:
                        x += 85
                    cover = os.path.join(coverdir, f'{music.id}.png')
                    if os.path.isfile(cover):
                        if str(music.lv) != 3:
                            cover_bg = diff[str(music.lv)]
                            cover_bg.alpha_composite(Image.open(cover).convert('RGBA').resize((65, 65)), (5, 5))
                        else:
                            cover_bg = Image.open(cover).convert('RGBA').resize((75, 75))
                        im.alpha_composite(cover_bg, (x, y))
                        if music.type == 'DX':
                            im.alpha_composite(dx, (x + 31, y))
                if not lvlist[lv]:
                    y += 85
            
            im.save(bg)
            log.info(f'lv.{ra} 定数表更新完成')
        return '定数表更新完成'
    except Exception as e:
        log.error(traceback.format_exc())
        return f'定数表更新失败，Error: {e}'


async def rating_table_draw(payload: dict, args: str) -> Union[str, MessageSegment, None]:
    payload['version'] = list(set(version for version in plate_to_version.values()))
    data = await get_player_data('plate', payload)
    if isinstance(data, str):
        return data
    
    if args in levelList[-3:]:
        bg = os.path.join(ratingdir, '14.png')
        ralist = levelList[-3:]
    else:
        bg = os.path.join(ratingdir, f'{args}.png')
        ralist = [args]
    
    fromid = {}
    for _data in data['verlist']:
        if _data['level'] in ralist:
            if (id := str(_data['id'])) not in fromid:
                fromid[id] = {}
            fromid[id][str(_data['level_index'])] = {
                'achievements': _data['achievements'],
                'level': _data['level']
            }

    musiclist = mai.total_list.lvList(True)
    lvlist: Dict[str, List[RaMusic]] = {}
    for lv in list(reversed(ralist)):
        for _ra in musiclist[lv]:
            lvlist[_ra] = musiclist[lv][_ra]
    
    im = Image.open(bg).convert('RGBA')
    b2 = Image.new('RGBA', (75, 75), (0, 0, 0, 64))
    y = 138
    for ra in lvlist:
        y += 10
        for num, music in enumerate(lvlist[ra]):
            if num % 15 == 0:
                x = 198
                y += 85
            else:
                x += 85
            if music.id in fromid and music.lv in fromid[music.id]:
                ra, rate = computeRa(music.ds, fromid[music.id][music.lv]['achievements'], israte=True)
                im.alpha_composite(b2, (x + 2, y - 18))
                rank = Image.open(os.path.join(maimaidir, f'UI_TTR_Rank_{rate}.png')).resize((78, 36))
                im.alpha_composite(rank, (x, y))
    
    msg = MessageSegment.image(image_to_base64(im))
    
    return msg