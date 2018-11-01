package main

import (
	"bytes"
	"encoding/binary"
)

// PacketReader ... Reads packets
type PacketReader struct {
	packet []byte
	offset uint16
}

func (pr *PacketReader) Byte() byte {
	defer func() {
		pr.offset++
	}()
	return byte(pr.packet[pr.offset])
}

func (pr *PacketReader) Short() uint16 {
	defer func() {
		pr.offset += 2
	}()
	return binary.LittleEndian.Uint16(pr.packet[pr.offset : pr.offset+2])
}

func (pr *PacketReader) Int() uint32 {
	defer func() {
		pr.offset += 4
	}()
	return binary.LittleEndian.Uint32(pr.packet[pr.offset : pr.offset+4])
}

func (pr *PacketReader) Long() uint64 {
	defer func() {
		pr.offset += 8
	}()
	return binary.LittleEndian.Uint64(pr.packet[pr.offset : pr.offset+8])
}

func (pr *PacketReader) String(len uint16) string {
	defer func() {
		pr.offset += len
	}()
	return string(pr.packet[pr.offset : pr.offset+len])
}

// PacketWriter ... Reads packets
type PacketWriter struct {
	packet *bytes.Buffer
	offset uint16
	size   uint16
	opcode uint16
}

// CreatePacketWriter ... PacketWriter constructor
func CreatePacketWriter(opcode int) *PacketWriter {
	pw := new(PacketWriter)
	pw.packet = new(bytes.Buffer)
	binary.Write(pw.packet, binary.LittleEndian, uint16(0))
	binary.Write(pw.packet, binary.LittleEndian, uint16(opcode))
	pw.offset = 2
	return pw
}

// Byte ... Convert byte to byter and write in packet
func (pw *PacketWriter) Byte(data byte) {
	defer func() {
		pw.offset++
	}()
	binary.Write(pw.packet, binary.LittleEndian, data)
}

// Short ... Convert short to byter and write in packet
func (pw *PacketWriter) Short(data uint16) {
	defer func() {
		pw.offset += 2
	}()
	binary.Write(pw.packet, binary.LittleEndian, data)
}

// Int ... Convert int to byter and write in packet
func (pw *PacketWriter) Int(data uint32) {
	defer func() {
		pw.offset += 4
	}()
	binary.Write(pw.packet, binary.LittleEndian, data)
}

// Long ... Convert long to byter and write in packet
func (pw *PacketWriter) Long(data uint64) {
	defer func() {
		pw.offset += 8
	}()
	binary.Write(pw.packet, binary.LittleEndian, data)
}

// String ... Convert string to byter and write in packet
func (pw *PacketWriter) String(data string) {
	strLen := uint16(len(data))
	defer func() {
		pw.offset += strLen
	}()
	//binary.Write(pw.packet, binary.LittleEndian, strLen)
	binary.Write(pw.packet, binary.LittleEndian, []byte(data))
}

// Send ... Send message from buffer
func (pw *PacketWriter) Send(conn *Conn) {
	binary.LittleEndian.PutUint16(pw.packet.Bytes()[0:2], pw.offset)
	conn.Write(pw.packet.Bytes())
}
