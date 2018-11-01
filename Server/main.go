package main

import (
	"encoding/binary"
	"fmt"
	"net"
	"time"

	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/sqlite"
)

func main() {
	serv := Server{addr: "0.0.0.0:5555", IdleTimeout: 55000}
	serv.maxOnline = 10
	serv.listen()
}

// Conn ... Class Conn
type Conn struct {
	net.Conn
	IdleTimeout time.Duration
	buffSize    int16
	uidConn     map[uint]*Conn
}

var groupIDuserIDs map[uint][]uint
var userIDgroupIDs map[uint][]uint
var userIDtoConn map[uint]*Conn

// Server ... Class of server
type Server struct {
	addr        string
	IdleTimeout time.Duration
	currOnline  int16
	maxOnline   int16
	uidConn     map[uint]*Conn
	db          *gorm.DB
}

func (s Server) getGroupMembers() {
	grMems := []GroupMemebers{}
	s.db.Find(&grMems)
	groupIDuserIDs = make(map[uint][]uint)
	userIDgroupIDs = make(map[uint][]uint)
	//grMems := []uint{}
	for _, grmem := range grMems {
		groupIDuserIDs[grmem.GID] = append(groupIDuserIDs[grmem.GID], grmem.UID)
		userIDgroupIDs[grmem.UID] = append(userIDgroupIDs[grmem.UID], grmem.GID)
	}
	//fmt.Println(userIDgroupIDs)
	//s.groupIDuserIDs[1] = grMems
}

func (s Server) listen() error {
	if s.addr == "" {
		s.addr = "127.0.0.1:5555"
	}

	db, err := gorm.Open("sqlite3", "test.db")
	db.AutoMigrate(&Account{}, &Group{}, &GroupMemebers{})
	s.db = db
	if err != nil {
		fmt.Println("Failed connect to database:", err)
		return err
	}
	s.getGroupMembers()

	listener, err := net.Listen("tcp", s.addr)
	if err != nil {
		return err
	}

	defer func() {
		listener.Close()
		db.Close()
	}()

	fmt.Printf("2k18 Messenger Server started on [%v]\n", s.addr)
	defer listener.Close()

	s.uidConn = make(map[uint]*Conn)

	for {
		if s.currOnline < s.maxOnline {
			newConn, err := listener.Accept()
			if err != nil {
				fmt.Println(err)
				continue
			}

			conn := &Conn{
				Conn:        newConn,
				IdleTimeout: s.IdleTimeout,
				buffSize:    10,
				uidConn:     s.uidConn,
			}

			go handle(conn, &s)
		}
	}
}

func handle(conn *Conn, serv *Server) error {
	defer func() {
		serv.currOnline--
		fmt.Printf("[%v] closed connection, online [%v]\n", conn.RemoteAddr(), serv.currOnline)
		conn.Close()
	}()
	serv.currOnline++
	fmt.Printf("[%v] new Connection, online [%v]\n", conn.RemoteAddr(), serv.currOnline)
	uid := uint(0)
	sess := &Session{conn: conn, db: serv.db}
	plenBuf := make([]byte, 2)
	for {
		_, err := conn.Read(plenBuf)
		if err != nil {
			serv.uidConn[uid] = nil
			fmt.Println("Packet size error:", err, "Uid:", uid)
			return err
		}
		plen := binary.LittleEndian.Uint16(plenBuf)

		packBuf := make([]byte, plen)
		_, err = conn.Read(packBuf)
		if err != nil {
			serv.uidConn[uid] = nil
			fmt.Println("Packet reading error:", err)
			return err
		}
		opcode := binary.LittleEndian.Uint16(packBuf[:2])

		reader := &PacketReader{
			packet: packBuf[2:plen],
			offset: 0,
		}

		switch opcode {
		case 4:
			uid = sess.Register(reader)
			fmt.Println("Reg uid", uid)
			if uid == 0 {
				sess.conn.Close()
			} else {
				serv.uidConn[uid] = sess.conn
			}
		case 10:
			sess.Contacts(reader)
		case 1:
			sess.Message(reader)
		case 2:
			sess.Sticker(reader)
		case 3:
			sess.CreateGroup(reader)
		case 5:
			sess.DelAddUserGroup(reader)
		case 6:
			sess.JoinGroup(reader)
		case 7:
			sess.GetGroups(reader)
		default:
			fmt.Println("No opcode found:", opcode)
		}
	}
}
