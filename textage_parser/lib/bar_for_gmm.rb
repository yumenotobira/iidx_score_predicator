require "nokogiri"

module TextageParser
  MAX_BEAT = 96
  class Bar
    attr_accessor :notes, :beat, :number, :soflans
    def initialize(table)
      @height = table.attributes["height"].value.to_i
      @beat = @height / 128.0
      @number = table.css("th").children.text.to_i
      # 0: ノーツなし, 1: ノーツあり
      @notes = Array.new(16){ Array.new(MAX_BEAT * @beat){ "0" } }
      @soflans = Array.new(MAX_BEAT * @beat){ 0 }
      table.css("img").each do |img|
        next unless img.attributes.has_key?("style")
        style = img.attributes["style"].value
        if soflan?(style)
          position = get_soflan_position(style)
          # BPMを保存
          new_bpm = img.next_sibling.children.text.to_i
          (position.to_i...(MAX_BEAT*@beat).to_i).each do |i|
            @soflans[i] = new_bpm if @soflans[i] == 0
          end
        else
          key_position = get_key_position(style)
          if cn?(style)
            cn_from, cn_to = get_cn_positions(style)
            [*(cn_from.to_i)..(cn_to.to_i)].each do |position|
              @notes[key_position][position] = "1"
            end
          else
            position = get_position(style)
            @notes[key_position][position] = "1"
          end
        end
      end

      # CNがあるときは普通のノートを置かない
      # CNの始点と終点にノートがないときは始点でも終点でもない
      (0..MAX_BEAT).each do |i|
        (0..7).each do |j|
          if @notes[j+8][i] == "1"
            if @notes[j][i] == "1"
              @notes[j][i] = "0"
            else
              @notes[j+8][i] = "1"
            end
          end
        end
      end
    end

    def encode_to_input
      result = ""
      (MAX_BEAT*@beat).to_i.times do |i|
        16.times do |j|
          result += @notes[j][i]
          result += ","
        end
        result += @soflans[i].to_s
        result += "\n"
      end
      result
    end

    private
    def get_key_position(style)
      # 0: 1鍵盤, 1: 2鍵盤, ..., 7: 皿
      # 8: 1鍵盤CN, 9: 2鍵盤CN, ..., 15: 7鍵盤CN, 16: 皿CN
      if cn?(style)
        left = style.match(/left:(\d+)px/)[1].to_i - 1
        return left / 14 + 8
      else
        left = style.match(/left:(\d+)px/)[1].to_i
        return left / 14
      end
    end

    def get_position(style)
      top = style.match(/top:(-?\d+)px/)[1].to_i
      a = @height - (top + 5)
      return a / (@height / (MAX_BEAT * @beat))
    end

    def get_cn_positions(style)
      top = style.match(/top:(-?\d+)px/)[1].to_i - 4
      height = style.match(/height:(\d+)px/)[1].to_i

      start = @height - (top + height + 5)
      owari = @height - (top + 5)
      [start / (@height / (MAX_BEAT * @beat)), owari / (@height / (MAX_BEAT * @beat))]
    end

    def get_soflan_position(style)
      top = style.match(/top:(-?\d+)px/)[1].to_i
      a = @height - (top + 2)
      return a / (@height / (MAX_BEAT * @beat))
    end

    def cn?(style)
      style.split(";").size == 4
    end

    def soflan?(style)
      style.split(";").size == 1
    end
  end

  def self.to_ZZ_format(n)
    sprintf("%02s", n.to_s(36)).gsub(/\s/, "0")
  end
end
